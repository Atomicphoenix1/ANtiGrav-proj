"""
textsplit.py  --  Standalone MP3 splitting utility.

Extracted from Super-Uploader.py (do_ffmpeg_split) for independent CLI use
and future GUI integration.  Fully self-contained; does not import Super-Uploader.py.

Usage (CLI):
    python textsplit.py --file <path>
    python textsplit.py --files <path1> <path2> ...
    python textsplit.py --folder <dir>
    python textsplit.py --file <path> --mode "10 min"
    python textsplit.py --file <path> --mode "Custom" --seconds 900
    python textsplit.py --file <path> --mode "Full (No Split)"

Usage (GUI):
    python textsplit.py
"""

import os
import sys
import shutil
import subprocess
import argparse
import gradio as gr

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "n8n_live_logs.txt")

# Gradio workspace -- files are staged here before being fed to the splitter
WORKSPACE = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Split-Vault"


def update_log(msg):
    """Print to terminal and append to n8n_live_logs.txt for real-time monitoring."""
    try:
        print(msg)
    except UnicodeEncodeError:
        sanitized = msg.encode("ascii", "replace").decode("ascii")
        print(sanitized)
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    return msg


# =========================================================================
# CORE SPLITTING ENGINE (Extracted precisely from Super-Uploader.py)
# =========================================================================
def do_ffmpeg_split(file_path, base_logs, split_mode="10 min", custom_seconds=600):
    """Splits or moves a single MP3 into part folders based on the split_mode selection."""
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    parent_dir = os.path.dirname(file_path)

    base_logs = update_log(f"📁 Preparing master folder for: {filename}")

    if "temp" in file_path.lower() or "appdata" in file_path.lower():
        target_folder = os.path.join(SCRIPT_DIR, base_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        new_file_path = os.path.join(target_folder, filename)
        shutil.copy2(file_path, new_file_path)
        base_logs = update_log(
            f"   ➡️ Copied temp file to workspace: {os.path.abspath(new_file_path)}"
        )
    else:
        if os.path.basename(parent_dir) == base_name:
            target_folder = parent_dir
            new_file_path = file_path
        else:
            target_folder = os.path.join(parent_dir, base_name)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            new_file_path = os.path.join(target_folder, filename)
            shutil.move(file_path, new_file_path)
            base_logs = update_log(
                f"   ➡️ Moved to folder: {os.path.abspath(new_file_path)}"
            )

    if split_mode == "Full (No Split)":
        part_dir = os.path.join(target_folder, "part001")
        if not os.path.exists(part_dir):
            os.makedirs(part_dir)
        dest_path = os.path.join(part_dir, "part001_seg001.mp3")
        shutil.copy2(new_file_path, dest_path)
        base_logs = update_log(
            "   ✅ Full mode selected (No Split). Created part001/part001_seg001.mp3."
        )
        return base_logs, target_folder

    # Determine segment time
    if split_mode == "10 min":
        seg_time = 600
    elif split_mode == "30 min":
        seg_time = 1800
    else:
        try:
            seg_time = int(custom_seconds)
        except ValueError:
            seg_time = 600

    # Split into temp files
    temp_pattern = os.path.join(target_folder, "temp_seg_%03d.mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        new_file_path,
        "-f",
        "segment",
        "-segment_time",
        str(seg_time),
        "-segment_start_number",
        "1",
        "-c",
        "copy",
        temp_pattern,
    ]
    try:
        base_logs = update_log(
            f"   ✂️ Slicing into {seg_time // 60}m {seg_time % 60}s segments..."
        )
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # Organize segments into part folders (pile up to 3 segments per folder)
        segments = sorted(
            [
                f
                for f in os.listdir(target_folder)
                if f.startswith("temp_seg_") and f.endswith(".mp3")
            ]
        )
        part_idx = 1
        for idx, seg_file in enumerate(segments, start=1):
            part_idx = (idx - 1) // 3 + 1
            seg_idx = (idx - 1) % 3 + 1
            part_dir = os.path.join(target_folder, f"part{part_idx:03d}")
            if not os.path.exists(part_dir):
                os.makedirs(part_dir)
            new_seg_name = f"part{part_idx:03d}_seg{seg_idx:03d}.mp3"
            shutil.move(
                os.path.join(target_folder, seg_file),
                os.path.join(part_dir, new_seg_name),
            )

        base_logs = update_log(
            f"   ✅ Segmentation complete! Organized into {part_idx} part folder(s) (<=3 segments per folder)."
        )
    except Exception as e:
        base_logs = update_log(f"   ❌ FFmpeg Error: {str(e)}")

    return base_logs, target_folder


def process_file(file_path, mode, custom_seconds):
    """Wraps the core split execution for clean log aggregation."""
    logs = ""
    filename = os.path.basename(file_path)
    logs += update_log("=" * 52) + "\n"
    logs += update_log(f"  🎬  {filename}")
    logs += update_log("=" * 52) + "\n"

    try:
        res_logs, out_folder = do_ffmpeg_split(
            file_path, "", split_mode=mode, custom_seconds=custom_seconds
        )
        logs += res_logs + "\n"
        logs += update_log(f"  ✅ Output master folder: {out_folder}") + "\n"
    except Exception as e:
        logs += update_log(f"  ❌ Process Failed: {str(e)}") + "\n"

    return logs


# =========================================================================
# GRADIO WRAPPER LAYER
# =========================================================================
def _stage_and_process(upload_item, mode, custom_seconds):
    """Safely transitions Gradio Temp files explicitly into your Workspace Drive before processing."""
    if upload_item is None:
        return ""

    # Support both dictionary format and class object variations across Gradio updates
    if isinstance(upload_item, dict):
        src_path = upload_item.get("path") or upload_item.get("name")
        orig_name = upload_item.get("orig_name")
    else:
        src_path = getattr(upload_item, "path", None) or getattr(upload_item, "name", None)
        orig_name = getattr(upload_item, "orig_name", None)

    if not src_path:
        return update_log("⚠️ Warning: Invalid upload item structure encountered.")

    if not orig_name:
        orig_name = os.path.basename(src_path)

    os.makedirs(WORKSPACE, exist_ok=True)
    workspace_path = os.path.join(WORKSPACE, orig_name)

    # Clean destination collision safely
    if os.path.exists(workspace_path):
        try:
            os.remove(workspace_path)
        except Exception:
            pass

    # STAGE IT TO WORKSPACE DRIVE
    shutil.copy2(src_path, workspace_path)

    # Core execution uses localized Workspace path mapping exclusively
    res = process_file(workspace_path, mode, custom_seconds)
    return res


def gradio_wrapper(scope, single_file, multi_files, folder_input, mode, custom_seconds):
    """Routes UI configurations cleanly to the processor engine."""
    # Ensure live tracking files clear cleanly on fresh sessions
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

    session_logs = update_log("🚀 TEXTSplit  --  Gradio Session")
    session_logs += update_log(f"   Mode: {mode}") + "\n"
    session_logs += "=" * 52 + "\n"

    try:
        custom_seconds = int(custom_seconds)
    except Exception:
        custom_seconds = 600

    if scope == "Single File":
        if not single_file:
            return session_logs + "❌ Error: Please upload an MP3 file first."
        session_logs += _stage_and_process(single_file, mode, custom_seconds)

    elif scope == "Multiple Files":
        if not multi_files:
            return session_logs + "❌ Error: Please select multiple files first."
        for item in multi_files:
            session_logs += _stage_and_process(item, mode, custom_seconds) + "\n"

    elif scope == "Folder":
        if not folder_input:
            return session_logs + "❌ Error: Please select a folder first."

        # Gradio 'directory' mode uploads files as a list of file objects
        # Filter out everything except valid .mp3 files
        mp3_files = []
        for item in folder_input:
            if isinstance(item, dict):
                filename = item.get("orig_name") or item.get("name") or ""
            else:
                filename = getattr(item, "orig_name", None) or getattr(item, "name", None) or ""
            
            if filename.lower().endswith(".mp3"):
                mp3_files.append(item)

        # Sort the folder items by their real file names
        def get_name(x):
            if isinstance(x, dict):
                return (x.get("orig_name") or os.path.basename(x.get("name") or "")).lower()
            return (getattr(x, "orig_name", None) or os.path.basename(getattr(x, "name", None) or "")).lower()

        mp3_files.sort(key=get_name)

        if not mp3_files:
            return session_logs + "❌ Error: No MP3 files found inside the selected directory."

        # Process each staged file through the safe workspace copy architecture
        for item in mp3_files:
            session_logs += _stage_and_process(item, mode, custom_seconds) + "\n"

    return session_logs


# =========================================================================
# COMMAND LINE ENTRY POINT
# =========================================================================
def main():
    parser = argparse.ArgumentParser(description="Standalone MP3 Split Engine")
    parser.add_argument("--file", help="Path to a single MP3 file")
    parser.add_argument("--files", nargs="+", help="Paths to multiple MP3 files")
    parser.add_argument("--folder", help="Path to directory containing MP3 files")
    parser.add_argument(
        "--mode",
        default="10 min",
        choices=["10 min", "30 min", "Full (No Split)", "Custom"],
        help="Split mode selection",
    )
    parser.add_argument(
        "--seconds", type=int, default=600, help="Custom duration segments (seconds)"
    )

    args = parser.parse_args()

    if args.file:
        process_file(args.file, args.mode, args.seconds)
    elif args.files:
        for f in args.files:
            process_file(f, args.mode, args.seconds)
    elif args.folder:
        if not os.path.isdir(args.folder):
            print(f"❌ Target directory not found: {args.folder}")
            return
        files = sorted(
            [
                os.path.join(args.folder, f)
                for f in os.listdir(args.folder)
                if f.lower().endswith(".mp3")
            ]
        )
        if not files:
            print("❌ No matching MP3 items located.")
            return
        for f in files:
            process_file(f, args.mode, args.seconds)
    else:
        parser.print_help()


# =========================================================================
# GRADIO GRAPHICAL INTERFACE LAYOUT
# =========================================================================
with gr.Blocks(title="TEXTSplit - Production Engine") as demo:
    gr.Markdown("# ✂️ Standalone MP3 Slicing Hub")
    gr.Markdown(
        f"Workspace Location Enforced: `{WORKSPACE}`. All logs update live below."
    )

    with gr.Row():
        with gr.Column(scale=1):
            scope = gr.Radio(
                choices=["Single File", "Multiple Files", "Folder"],
                value="Single File",
                label="Execution Scope",
            )

            # FIXED: gr.Box changed to gr.Group for modern Gradio versions compatibility
            with gr.Group() as single_col:
                single_file = gr.File(
                    label="Drop Single MP3 Here",
                    file_types=[".mp3"],
                    file_count="single",
                )

            with gr.Group(visible=False) as multi_col:
                multi_files = gr.File(
                    label="Drop Multiple MP3s Here",
                    file_types=[".mp3"],
                    file_count="multiple",
                )

            with gr.Group(visible=False) as folder_col:
                folder_input = gr.File(
                    label="Select Local Folder",
                    file_count="directory"
                )

            gr.Markdown("---")
            mode_dd = gr.Dropdown(
                choices=["10 min", "30 min", "Full (No Split)", "Custom"],
                value="10 min",
                label="Split Mode",
            )
            custom_sec = gr.Number(
                value=600,
                label="Custom Seconds (only for Custom mode)",
            )
            run_btn = gr.Button("🚀 Run Splitter", variant="primary")

        with gr.Column(scale=2):
            log_box = gr.Textbox(
                label="Live Terminal Log",
                interactive=False,
                lines=25,
            )

    # --- Visibility toggles ---
    def _toggle_inputs(choice):
        return [
            gr.update(visible=(choice == "Single File")),
            gr.update(visible=(choice == "Multiple Files")),
            gr.update(visible=(choice == "Folder")),
        ]

    scope.change(
        _toggle_inputs,
        scope,
        [single_col, multi_col, folder_col],
    )

    # --- Run button ---
    run_btn.click(
        fn=gradio_wrapper,
        inputs=[scope, single_file, multi_files, folder_input, mode_dd, custom_sec],
        outputs=log_box,
    )


# =========================================================================
# DUAL MODE ENTRY EXECUTION
# =========================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        demo.launch(inbrowser=True)