#!/usr/bin/env python3
"""
mdconver.py — Batch document-to-Markdown converter using the Anthropic API.

PROCESSING STRATEGY (hybrid):
  1. Try sending the whole document in one API call.
  2. If the API rejects it (input context overflow), automatically fall back
     to page-chunked mode:
       a. Split the PDF into PAGES_PER_CHUNK-page sub-PDFs.
       b. Call the API once per chunk — extract Section 2 Markdown only.
       c. One final synthesis pass — generate Sections 0 and 1 (summary +
          schema extraction) from the assembled Section 2 text.
       d. Combine everything into the final .md file.

In both modes, output continuation handles max_tokens (output overflow):
  if stop_reason == "max_tokens" → re-call with the partial output as
  the assistant turn and ask Claude to continue exactly where it left off.

Token tracking: every API call logs input/output tokens. Per-file and
session summary logs are written to Outputs/logs/.
"""

import anthropic
import base64
import datetime
import io
import json
import os
from typing import Dict, List, Optional, Tuple
import sys
import threading
import time
import traceback

# ── Optional libraries ─────────────────────────────────────────────────────────
try:
    from pypdf import PdfReader, PdfWriter
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from pptx import Presentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import openpyxl
    HAS_XLSX = True
except ImportError:
    HAS_XLSX = False

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))

def _load_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("AI_MODEL_MODEL_ANTHROPIC_KEY", "")
    if not key:
        env_path = os.path.join(BASE_DIR, ".env.local")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("ANTHROPIC_API_KEY=") or line.startswith("AI_MODEL_MODEL_ANTHROPIC_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment or .env.local")
    return key

API_KEY = _load_api_key()
MODEL       = "claude-opus-4-5"
PDF_DIR     = os.path.join(BASE_DIR, "PDFs")
PROMPT_PATH = os.path.join(BASE_DIR, "Prompt", "prompt_file.md")
OUTPUT_DIR  = os.path.join(BASE_DIR, "Outputs")
LOG_DIR     = os.path.join(OUTPUT_DIR, "logs")

MAX_TOKENS_PER_PASS = 16000   # max output tokens per API call
MAX_PASSES          = 12      # safety cap on output continuation loops
PAGES_PER_CHUNK     = 15      # pages per chunk in chunked fallback mode
MAX_CONNECTION_RETRIES = 3    # retries for transient connection errors

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".xlsx", ".xls"}

# ── Logging ───────────────────────────────────────────────────────────────────

def _make_log_path(filename: str) -> str:
    ts        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem      = os.path.splitext(filename)[0]
    safe_stem = "".join(c if c.isalnum() or c in " _-()." else "_" for c in stem).strip()
    return os.path.join(LOG_DIR, f"{ts}_{safe_stem}.log")


class RunLogger:
    """Accumulates structured log entries and writes a final summary."""

    def __init__(self, source_filename: str):
        self.source_filename = source_filename
        self.log_path        = _make_log_path(source_filename)
        self.start_time      = datetime.datetime.now()
        self.entries: List[Dict] = []
        self.total_input_tokens  = 0
        self.total_output_tokens = 0
        self._lines: List[str]   = []
        self.mode = "whole-pdf"   # updated to "chunked" if fallback triggered

    def log(self, msg: str):
        ts   = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line, flush=True)
        self._lines.append(line)

    def record_call(self, label: str, pass_num: int,
                    input_tok: int, output_tok: int,
                    stop_reason: str, chars_generated: int):
        self.total_input_tokens  += input_tok
        self.total_output_tokens += output_tok
        entry = {
            "label":           label,
            "pass":            pass_num,
            "input_tokens":    input_tok,
            "output_tokens":   output_tok,
            "stop_reason":     stop_reason,
            "chars_generated": chars_generated,
        }
        self.entries.append(entry)
        self.log(
            f"  [{label} / pass {pass_num}] "
            f"in:{input_tok:,} tok  out:{output_tok:,} tok  "
            f"chars:{chars_generated:,}  stop:{stop_reason}"
        )

    def write(self, output_path: Optional[str], error: Optional[str] = None):
        os.makedirs(LOG_DIR, exist_ok=True)
        end_time = datetime.datetime.now()
        elapsed  = (end_time - self.start_time).total_seconds()

        with open(self.log_path, "w", encoding="utf-8") as f:
            f.write("=" * 72 + "\n")
            f.write(" mdconver.py — Run Log\n")
            f.write("=" * 72 + "\n\n")
            f.write(f"Source file   : {self.source_filename}\n")
            f.write(f"Model         : {MODEL}\n")
            f.write(f"Mode          : {self.mode}\n")
            f.write(f"Run started   : {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Run finished  : {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Elapsed       : {elapsed:.1f}s\n")
            f.write(f"Output file   : {output_path or 'N/A (error)'}\n\n")

            f.write("-" * 72 + "\n")
            f.write(" Per-Call Token Summary\n")
            f.write("-" * 72 + "\n")
            f.write(f"{'Label':<30} {'Pass':>5}  {'Input':>10}  {'Output':>10}  {'Chars':>9}  Stop\n")
            f.write(f"{'-'*30} {'----':>5}  {'--------':>10}  {'--------':>10}  {'-----':>9}  ----\n")
            for e in self.entries:
                f.write(
                    f"{e['label']:<30} {e['pass']:>5}  {e['input_tokens']:>10,}  "
                    f"{e['output_tokens']:>10,}  {e['chars_generated']:>9,}  {e['stop_reason']}\n"
                )
            f.write(f"\n{'TOTAL':<30} {'':>5}  {self.total_input_tokens:>10,}  {self.total_output_tokens:>10,}\n\n")

            f.write("-" * 72 + "\n")
            f.write(" Console Output\n")
            f.write("-" * 72 + "\n")
            for line in self._lines:
                f.write(line + "\n")

            if error:
                f.write("\n" + "=" * 72 + "\n ERROR\n" + "=" * 72 + "\n")
                f.write(error + "\n")

        self.log(f"  Log saved → {self.log_path}")
        self.log(
            f"  TOTAL TOKENS — "
            f"input:{self.total_input_tokens:,}  "
            f"output:{self.total_output_tokens:,}  "
            f"combined:{self.total_input_tokens + self.total_output_tokens:,}"
        )


# ── File helpers ──────────────────────────────────────────────────────────────

def load_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def load_pdf_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_pdf_page_count(path: str) -> int:
    if not HAS_PYPDF:
        raise RuntimeError("pypdf not installed. Run: pip install pypdf")
    return len(PdfReader(path).pages)


def extract_pages_b64(path: str, start: int, end: int) -> str:
    """Return a base64-encoded sub-PDF containing pages [start, end) (0-indexed)."""
    reader = PdfReader(path)
    writer = PdfWriter()
    for i in range(start, min(end, len(reader.pages))):
        writer.add_page(reader.pages[i])
    buf = io.BytesIO()
    writer.write(buf)
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


def pptx_to_text(path: str) -> str:
    if not HAS_PPTX:
        raise RuntimeError("python-pptx not installed.")
    prs   = Presentation(path)
    lines = []
    for n, slide in enumerate(prs.slides, 1):
        lines.append(f"\n--- SLIDE {n} ---\n")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                lines.append(shape.text.strip())
            if shape.shape_type == 19:
                for row in shape.table.rows:
                    lines.append("  |  ".join(c.text.strip() for c in row.cells))
    return "\n".join(lines)


def docx_to_text(path: str) -> str:
    if not HAS_DOCX:
        raise RuntimeError("python-docx not installed.")
    doc = docx.Document(path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            lines.append("  |  ".join(c.text.strip() for c in row.cells))
    return "\n".join(lines)


def xlsx_to_text(path: str) -> str:
    if not HAS_XLSX:
        raise RuntimeError("openpyxl not installed.")
    wb    = openpyxl.load_workbook(path, data_only=True)
    lines = []
    for name in wb.sheetnames:
        lines.append(f"\n=== SHEET: {name} ===\n")
        for row in wb[name].iter_rows(values_only=True):
            row_text = "  |  ".join("" if c is None else str(c) for c in row)
            if row_text.strip("|").strip():
                lines.append(row_text)
    return "\n".join(lines)


def _build_doc_block(file_path: str) -> dict:
    """Return the Anthropic content block for a whole document."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": load_pdf_b64(file_path)},
        }
    if ext == ".pptx":   text, label = pptx_to_text(file_path), "PowerPoint"
    elif ext == ".docx": text, label = docx_to_text(file_path),  "Word document"
    elif ext in (".xlsx", ".xls"): text, label = xlsx_to_text(file_path), "Excel spreadsheet"
    else: raise ValueError(f"Unsupported type: {ext}")
    return {"type": "text", "text": f"[Source: {label}]\n\n{text}"}


def _build_chunk_doc_block(file_path: str, start: int, end: int) -> dict:
    """Return a document block for a page-range sub-PDF."""
    return {
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf",
                   "data": extract_pages_b64(file_path, start, end)},
    }


# ── Prompts ───────────────────────────────────────────────────────────────────

CONTINUATION_INSTRUCTION = """\
Your output was cut off because you reached the output token limit.
CONTINUE from EXACTLY where you left off. Rules:
- Do NOT repeat any content already written above.
- Do NOT restart from the beginning. Do NOT add any preamble.
- Jump straight back into the content and continue until complete.
"""

def _chunk_section2_prompt(start_page: int, end_page: int, total_pages: int) -> str:
    return f"""\
You are processing pages {start_page}–{end_page} of a {total_pages}-page document.

Your ONLY task: extract the FULL MARKDOWN content for these pages.
This is SECTION 2 content only — do NOT generate a summary, schema, or header block.

Follow all formatting rules from the main prompt:
- Insert <!-- PAGE: N --> before each page and --- between pages.
- Convert every table to a Markdown table with a heading and 2–4 sentence explanation.
- Describe every chart and image with the standard block format.
- Reproduce ALL body text word-for-word — no summaries, no ellipses.
- Include all footnotes and disclaimers exactly as written.

Begin your output directly with <!-- PAGE: {start_page} --> and continue through page {end_page}.
"""

def _synthesis_prompt(prompt_text: str) -> str:
    return f"""\
{prompt_text}

────────────────────────────────────────────────────────────
IMPORTANT INSTRUCTION FOR THIS CALL:

The SECTION 2 full-document Markdown has already been extracted and assembled
for you below this message. It is complete — do NOT re-extract it.

Your task is ONLY to produce the following and nothing else:
1. The document header block (Fund name, extraction date, schema identification, LLM reading instructions)
2. SECTION 0 — INVESTMENT PROFESSIONAL SUMMARY
3. SECTION 0B — INVESTMENT DECISION SUMMARY
4. SECTION 1 — EXTRACTED SCHEMA DATA

After completing Section 1, output the exact text:
  __SECTIONS_01_COMPLETE__

Then stop. Do NOT reproduce Section 2.
────────────────────────────────────────────────────────────
"""


# ── Core API call helper ──────────────────────────────────────────────────────

def _stream_with_continuation(
    client: anthropic.Anthropic,
    messages: list,
    label: str,
    logger: RunLogger,
) -> str:
    """
    Stream an API call. If stop_reason == "max_tokens", automatically
    continue (append assistant + user continuation turns) until end_turn.
    Returns the full accumulated text.
    """
    accumulated = ""
    pass_num    = 0

    while pass_num < MAX_PASSES:
        pass_num += 1
        logger.log(f"  [{label}] Starting pass {pass_num} …")

        # Heartbeat thread
        _stop_hb = threading.Event()
        def _heartbeat(lbl=label, pn=pass_num):
            count = 0
            while not _stop_hb.wait(10):
                count += 1
                print(f"  [{lbl} / pass {pn}] … API call in progress ({count * 10}s elapsed) …",
                      flush=True)
        hb = threading.Thread(target=_heartbeat, daemon=True)
        hb.start()

        pass_text     = ""
        stop_reason   = None
        input_tokens  = 0
        output_tokens = 0

        try:
            with client.messages.stream(
                model=MODEL,
                max_tokens=MAX_TOKENS_PER_PASS,
                messages=messages,
            ) as stream:
                chunk_count = 0
                for text_chunk in stream.text_stream:
                    pass_text   += text_chunk
                    chunk_count += 1
                    if chunk_count % 200 == 0:
                        logger.log(f"  [{label}] … streaming: {len(accumulated) + len(pass_text):,} chars …")
                final_msg     = stream.get_final_message()
                stop_reason   = final_msg.stop_reason
                input_tokens  = final_msg.usage.input_tokens
                output_tokens = final_msg.usage.output_tokens
        except anthropic.APIConnectionError as conn_err:
            _stop_hb.set()
            if not hasattr(_stream_with_continuation, '_retry_count'):
                _stream_with_continuation._retry_count = 0
            _stream_with_continuation._retry_count += 1
            if _stream_with_continuation._retry_count <= MAX_CONNECTION_RETRIES:
                wait = 2 ** _stream_with_continuation._retry_count
                logger.log(f"  [{label}] Connection error: {conn_err}. Retrying in {wait}s… (attempt {_stream_with_continuation._retry_count}/{MAX_CONNECTION_RETRIES})")
                time.sleep(wait)
                pass_num -= 1  # don't count this as a pass
                continue
            else:
                _stream_with_continuation._retry_count = 0
                raise
        finally:
            _stop_hb.set()

        # Reset retry counter on success
        _stream_with_continuation._retry_count = 0

        logger.record_call(label, pass_num, input_tokens, output_tokens,
                           stop_reason, len(pass_text))
        accumulated += pass_text

        if stop_reason == "end_turn":
            logger.log(f"  [{label}] Complete after {pass_num} pass(es).")
            break
        elif stop_reason == "max_tokens":
            logger.log(f"  [{label}] Output truncated — running continuation pass …")
            # Build continuation: original messages + assistant output so far + continue prompt
            messages = messages + [
                {"role": "assistant", "content": accumulated},
                {"role": "user",      "content": CONTINUATION_INSTRUCTION},
            ]
        else:
            logger.log(f"  [{label}] Unexpected stop_reason: {stop_reason}. Stopping.")
            break

    return accumulated


# ── Strategy A: Whole-document ─────────────────────────────────────────────────

def _run_whole_doc(
    file_path: str,
    prompt_text: str,
    logger: RunLogger,
    client: anthropic.Anthropic,
) -> str:
    """Send the entire document in one shot (with output continuation)."""
    logger.log("Strategy: whole-document (single API call)")
    doc_block = _build_doc_block(file_path)
    messages  = [{"role": "user", "content": [
        doc_block,
        {"type": "text", "text": prompt_text},
    ]}]
    return _stream_with_continuation(client, messages, "whole-doc", logger)


# ── Strategy B: Page-chunked ───────────────────────────────────────────────────

def _run_chunked(
    file_path: str,
    prompt_text: str,
    logger: RunLogger,
    client: anthropic.Anthropic,
) -> str:
    """
    Chunked fallback:
      1. Extract Section 2 page-by-page in batches.
      2. One synthesis pass for Sections 0+1.
      3. Assemble into final output.
    """
    logger.mode = "chunked"
    total_pages = get_pdf_page_count(file_path)
    logger.log(f"Strategy: chunked ({total_pages} pages, {PAGES_PER_CHUNK} pages/chunk)")

    section2_parts: List[str] = []
    chunk_idx = 0

    for start in range(0, total_pages, PAGES_PER_CHUNK):
        end       = min(start + PAGES_PER_CHUNK, total_pages)
        chunk_idx += 1
        label     = f"chunk-{chunk_idx} (pp{start+1}-{end})"
        logger.log(f"Processing {label} …")

        doc_block = _build_chunk_doc_block(file_path, start, end)
        chunk_prompt = _chunk_section2_prompt(start + 1, end, total_pages)
        messages  = [{"role": "user", "content": [
            doc_block,
            {"type": "text", "text": chunk_prompt},
        ]}]
        chunk_text = _stream_with_continuation(client, messages, label, logger)
        section2_parts.append(chunk_text.strip())

    # Assemble Section 2
    full_section2 = "\n\n".join(section2_parts)
    logger.log(f"Section 2 assembled: {len(full_section2):,} chars from {chunk_idx} chunk(s)")

    # Final synthesis pass: generate Sections 0 + 1
    logger.log("Running synthesis pass (Sections 0 + 1) …")
    synth_prompt = _synthesis_prompt(prompt_text)

    # Truncate section2 text if enormous (keep first 120k chars which is ~90k tokens)
    section2_for_synth = full_section2[:120_000]
    if len(full_section2) > 120_000:
        logger.log(f"  Section 2 truncated to 120,000 chars for synthesis pass.")

    synth_messages = [{"role": "user", "content": [
        {"type": "text", "text": f"{synth_prompt}\n\n---\n\n{section2_for_synth}"},
    ]}]
    sections_01 = _stream_with_continuation(client, synth_messages, "synthesis", logger)

    # Strip the sentinel marker if present
    sections_01 = sections_01.replace("__SECTIONS_01_COMPLETE__", "").rstrip()

    # Build final output: header+sections 0&1 + section 2
    final_output = (
        sections_01.rstrip()
        + "\n\n---\n\n"
        + "# SECTION 2 — FULL DOCUMENT MARKDOWN\n\n"
        + "> This section contains the complete Markdown conversion of the source document.\n\n"
        + full_section2
    )
    return final_output


# ── Main entry per file ───────────────────────────────────────────────────────

def run_single_file(file_path: str, prompt_text: str, logger: RunLogger) -> str:
    """
    Try whole-document approach first. If the API rejects due to input
    context overflow, automatically fall back to chunked mode.
    """
    client = anthropic.Anthropic(api_key=API_KEY)

    try:
        return _run_whole_doc(file_path, prompt_text, logger, client)

    except anthropic.BadRequestError as e:
        msg = str(e).lower()
        if any(kw in msg for kw in ("too large", "context", "length", "exceeds", "tokens")):
            logger.log(f"⚠️  Input too large for whole-doc mode: {e}")
            logger.log("Switching to chunked mode …")
            ext = os.path.splitext(file_path)[1].lower()
            if ext != ".pdf":
                raise RuntimeError(
                    "Chunked fallback is only supported for PDF files. "
                    "Non-PDF file is too large for the API."
                ) from e
            return _run_chunked(file_path, prompt_text, logger, client)
        raise  # Re-raise for unrelated BadRequestErrors


# ── Batch runner ──────────────────────────────────────────────────────────────

def convert_file(file_path: str, prompt_text: str) -> dict:
    filename    = os.path.basename(file_path)
    stem        = os.path.splitext(filename)[0]
    output_path = os.path.join(OUTPUT_DIR, stem + ".md")
    logger      = RunLogger(filename)

    logger.log("=" * 62)
    logger.log(f"Processing : {filename}")
    logger.log(f"Output     : {output_path}")
    logger.log(f"Chunk size : {PAGES_PER_CHUNK} pages (chunked fallback)")

    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        md_text = run_single_file(file_path, prompt_text, logger)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_text)

        logger.log(f"✅ Saved → {output_path}  ({len(md_text):,} chars)")
        logger.write(output_path)
        return {
            "file": filename, "output": output_path, "success": True,
            "mode": logger.mode, "passes": len(logger.entries),
            "total_input_tokens":  logger.total_input_tokens,
            "total_output_tokens": logger.total_output_tokens,
            "log": logger.log_path,
        }

    except Exception as exc:
        err = traceback.format_exc()
        logger.log(f"❌ ERROR: {exc}")
        logger.write(None, error=err)
        return {
            "file": filename, "success": False,
            "error": str(exc), "log": logger.log_path,
        }


def main(target_files: Optional[List[str]] = None):
    prompt_text = load_prompt()
    print(f"Prompt loaded: {len(prompt_text):,} chars", flush=True)
    print(f"Mode: hybrid (whole-doc → chunked fallback, {PAGES_PER_CHUNK} pp/chunk)", flush=True)

    if target_files:
        files = [f if os.path.isabs(f) else os.path.join(PDF_DIR, f)
                 for f in target_files]
    else:
        files = sorted([
            os.path.join(PDF_DIR, f) for f in os.listdir(PDF_DIR)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS
        ])

    if not files:
        print("No supported files found. Nothing to do.", flush=True)
        return

    print(f"Files to process: {len(files)}", flush=True)
    for f in files:
        print(f"  • {os.path.basename(f)}", flush=True)
    print(flush=True)

    results             = []
    grand_input_tokens  = 0
    grand_output_tokens = 0

    for file_path in files:
        result = convert_file(file_path, prompt_text)
        results.append(result)
        grand_input_tokens  += result.get("total_input_tokens",  0)
        grand_output_tokens += result.get("total_output_tokens", 0)
        print(flush=True)

    # Session summary
    print("=" * 62, flush=True)
    print("SESSION SUMMARY", flush=True)
    print("=" * 62, flush=True)
    for r in results:
        icon = "✅" if r["success"] else "❌"
        info = (
            f"mode:{r.get('mode','?')}  "
            f"in:{r.get('total_input_tokens', 0):,}  "
            f"out:{r.get('total_output_tokens', 0):,}  "
            f"calls:{r.get('passes', '?')}"
        ) if r["success"] else f"ERROR: {r.get('error', '')}"
        print(f"  {icon}  {r['file']:<55} {info}", flush=True)
        print(f"       Log → {r.get('log', 'N/A')}", flush=True)

    print(flush=True)
    print(f"  Grand total input tokens  : {grand_input_tokens:,}",  flush=True)
    print(f"  Grand total output tokens : {grand_output_tokens:,}", flush=True)
    print(f"  Grand total combined      : {grand_input_tokens + grand_output_tokens:,}", flush=True)
    print("=" * 62, flush=True)

    ts          = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_log = os.path.join(LOG_DIR, f"{ts}_session_summary.json")
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(session_log, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp":           ts,
            "model":               MODEL,
            "pages_per_chunk":     PAGES_PER_CHUNK,
            "files_processed":     len(results),
            "grand_input_tokens":  grand_input_tokens,
            "grand_output_tokens": grand_output_tokens,
            "grand_total_tokens":  grand_input_tokens + grand_output_tokens,
            "results":             results,
        }, f, indent=2)
    print(f"  Session JSON → {session_log}", flush=True)


if __name__ == "__main__":
    cli_targets = sys.argv[1:] if len(sys.argv) > 1 else None
    main(cli_targets)
