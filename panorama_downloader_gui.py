#!/usr/bin/env python3
"""
Unified Panorama Downloader GUI
Downloads and stitches panoramas from Street View URLs or custom template URLs.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import sys
import re
import requests
import urllib.parse
from pathlib import Path
from PIL import Image
import subprocess
import os
import time
import shutil
from datetime import datetime


class PanoramaDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Panorama Downloader")
        self.root.geometry("800x750")
        self.root.resizable(True, True)
        
        # Progress tracking
        self.progress_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        self.start_time = None
        
        # Variables
        self.url_type_var = tk.StringVar(value="streetview")
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value=str(Path.home() / "Desktop" / "Panoramas"))
        self.pano_name_var = tk.StringVar(value=self.get_default_name())
        self.mode_var = tk.StringVar(value="full")
        self.zoom_mode_var = tk.StringVar(value="auto")
        self.zoom_level_var = tk.IntVar(value=5)
        self.open_folder_var = tk.BooleanVar(value=True)
        self.delete_tiles_var = tk.BooleanVar(value=True)
        self.timer_var = tk.StringVar(value="")
        
        self.setup_ui()
        self.start_progress_monitor()
        
    def get_default_name(self):
        """Generate default name with current timestamp."""
        return datetime.now().strftime("%Y%m%d%H%M%S")
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # URL Type Selection
        url_type_frame = ttk.LabelFrame(main_frame, text="URL Type", padding="10")
        url_type_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        row += 1
        
        ttk.Radiobutton(url_type_frame, text="Google Street View URL", 
                       variable=self.url_type_var, value="streetview",
                       command=self.on_url_type_change).grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        ttk.Radiobutton(url_type_frame, text="Custom Template URL (with [%X] and [%Y] placeholders)", 
                       variable=self.url_type_var, value="template",
                       command=self.on_url_type_change).grid(row=0, column=1, sticky=tk.W)
        
        # URL Input
        self.url_label = ttk.Label(main_frame, text="Google Maps Street View URL:")
        self.url_label.grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        row += 1
        
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=80)
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(url_frame, text="Paste", command=self.paste_url).grid(row=0, column=1)
        row += 1
        
        # Example label for template URLs
        self.example_label = ttk.Label(main_frame, text="", foreground="gray")
        self.example_label.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Output Directory and Panorama Name
        settings_frame = ttk.LabelFrame(main_frame, text="Output Settings", padding="10")
        settings_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        settings_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Output Directory
        ttk.Label(settings_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        dir_frame = ttk.Frame(settings_frame)
        dir_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        dir_frame.columnconfigure(0, weight=1)
        
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=60)
        self.dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(dir_frame, text="Browse...", command=self.browse_directory).grid(row=0, column=1)
        
        # Panorama Name
        ttk.Label(settings_frame, text="Panorama Name:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        name_frame = ttk.Frame(settings_frame)
        name_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        name_frame.columnconfigure(0, weight=1)
        
        self.name_entry = ttk.Entry(name_frame, textvariable=self.pano_name_var, width=40)
        self.name_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(name_frame, text="Generate New", command=self.generate_new_name).grid(row=0, column=1)
        
        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))
        options_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Mode selection
        ttk.Label(options_frame, text="Mode:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Radiobutton(mode_frame, text="Full Pipeline", variable=self.mode_var, value="full").grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="Download Only", variable=self.mode_var, value="download").grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="Normalize Only", variable=self.mode_var, value="normalize").grid(row=1, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(mode_frame, text="Stitch Only", variable=self.mode_var, value="stitch").grid(row=1, column=1, sticky=tk.W)
        
        # Zoom selection (only for Street View)
        self.zoom_label = ttk.Label(options_frame, text="Zoom:")
        self.zoom_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.zoom_frame = ttk.Frame(options_frame)
        self.zoom_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        ttk.Radiobutton(self.zoom_frame, text="Auto (5→4 fallback)", variable=self.zoom_mode_var, value="auto").grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        
        manual_frame = ttk.Frame(self.zoom_frame)
        manual_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(manual_frame, text="Force Zoom:", variable=self.zoom_mode_var, value="manual").grid(row=0, column=0, sticky=tk.W)
        zoom_combo = ttk.Combobox(manual_frame, textvariable=self.zoom_level_var, values=[0, 1, 2, 3, 4, 5], width=5, state="readonly")
        zoom_combo.grid(row=0, column=1, padx=(5, 0))
        
        # Other options
        ttk.Checkbutton(options_frame, text="Open result folder when complete", variable=self.open_folder_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        ttk.Checkbutton(options_frame, text="Delete tile folder after stitching", variable=self.delete_tiles_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Start button
        self.start_button = ttk.Button(main_frame, text="Start Download", command=self.start_download)
        self.start_button.grid(row=row, column=0, columnspan=3, pady=(0, 15))
        row += 1
        
        # Progress Frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=row, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        progress_frame.rowconfigure(4, weight=1)
        
        # Status and timer
        status_frame = ttk.Frame(progress_frame)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(status_frame, textvariable=self.timer_var, foreground="blue").grid(row=0, column=1, sticky=tk.E)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Current operation
        self.current_var = tk.StringVar(value="")
        self.current_label = ttk.Label(progress_frame, textvariable=self.current_var)
        self.current_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        
        # Log
        log_header = ttk.Frame(progress_frame)
        log_header.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        log_header.columnconfigure(0, weight=1)
        
        ttk.Label(log_header, text="Log:").grid(row=0, column=0, sticky=tk.W)
        ttk.Button(log_header, text="Clear Log", command=self.clear_log).grid(row=0, column=1)
        
        # Log text with scrollbar
        log_frame = ttk.Frame(progress_frame)
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        row += 1
        
        # Bottom buttons
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=row, column=0, columnspan=3, sticky=tk.E)
        
        ttk.Button(bottom_frame, text="Help", command=self.show_help).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(bottom_frame, text="About", command=self.show_about).grid(row=0, column=1)
        
        # Initialize UI state
        self.on_url_type_change()
    
    def on_url_type_change(self):
        """Update UI based on selected URL type."""
        if self.url_type_var.get() == "streetview":
            self.url_label.config(text="Google Maps Street View URL:")
            self.example_label.config(text="")
            # Show zoom options
            self.zoom_label.grid()
            self.zoom_frame.grid()
        else:
            self.url_label.config(text="Custom Template URL:")
            self.example_label.config(text="Example: https://example.com/tile?x=[%X]&y=[%Y]&z=5")
            # Hide zoom options for template URLs
            self.zoom_label.grid_remove()
            self.zoom_frame.grid_remove()
    
    def paste_url(self):
        try:
            clipboard_content = self.root.clipboard_get()
            if clipboard_content:
                self.url_var.set(clipboard_content)
                self.log("URL pasted from clipboard")
            else:
                messagebox.showwarning("Clipboard Error", "Clipboard is empty")
        except tk.TclError:
            messagebox.showwarning("Clipboard Error", "Could not access clipboard")
    
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def generate_new_name(self):
        self.pano_name_var.set(self.get_default_name())
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def check_name_conflict(self, output_dir, pano_name):
        """Check if panorama name already exists and handle conflict."""
        output_path = Path(output_dir)
        panorama_file = output_path / f"{pano_name}_panorama.jpg"
        
        if panorama_file.exists():
            result = messagebox.askyesnocancel(
                "File Already Exists",
                f"A panorama named '{pano_name}_panorama.jpg' already exists.\n\n"
                "Would you like to:\n"
                "• Yes: Overwrite the existing file\n"
                "• No: Choose a different name\n"
                "• Cancel: Abort the operation"
            )
            
            if result is None:  # Cancel
                return "cancel"
            elif result:  # Yes - overwrite
                return "overwrite"
            else:  # No - rename
                return "rename"
        
        return "ok"
    
    def start_download(self):
        if self.is_running:
            return
        
        # Validate inputs
        url = self.url_var.get().strip()
        output_dir = self.output_dir_var.get().strip()
        pano_name = self.pano_name_var.get().strip()
        url_type = self.url_type_var.get()
        
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
        
        if not output_dir:
            messagebox.showerror("Error", "Please select an output directory")
            return
        
        if not pano_name:
            messagebox.showerror("Error", "Please enter a panorama name")
            return
        
        # Validate URL format
        if url_type == "streetview":
            if not url.startswith("http"):
                messagebox.showerror("Error", "Please enter a valid Google Maps URL")
                return
        else:  # template
            if '[%X]' not in url or '[%Y]' not in url:
                messagebox.showerror("Error", "Template URL must contain [%X] and [%Y] placeholders")
                return
        
        # Check for name conflicts
        conflict_result = self.check_name_conflict(output_dir, pano_name)
        if conflict_result == "cancel":
            return
        elif conflict_result == "rename":
            # Focus on the name entry for user to change it
            self.name_entry.focus()
            self.name_entry.select_range(0, tk.END)
            return
        
        # Start timer
        self.start_time = time.time()
        
        # Start worker thread
        self.is_running = True
        self.start_button.config(text="Running...", state="disabled")
        
        # Prepare arguments
        args = {
            'url': url,
            'url_type': url_type,
            'output_dir': output_dir,
            'pano_name': pano_name,
            'mode': self.mode_var.get(),
            'zoom_mode': self.zoom_mode_var.get(),
            'zoom_level': self.zoom_level_var.get(),
            'open_folder': self.open_folder_var.get(),
            'delete_tiles': self.delete_tiles_var.get()
        }
        
        self.worker_thread = threading.Thread(target=self.worker_function, args=(args,))
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def worker_function(self, args):
        temp_dir = None
        try:
            # Setup
            output_dir = Path(args['output_dir'])
            output_dir.mkdir(exist_ok=True)
            
            url = args['url']
            url_type = args['url_type']
            pano_name = args['pano_name']
            mode = args['mode']
            
            self.update_progress("Starting...", 0)
            
            if url_type == "streetview":
                # Street View workflow
                zoom = None if args['zoom_mode'] == 'auto' else args['zoom_level']
                
                if mode == "full":
                    # Extract panoid
                    self.update_progress("Extracting panoid...", 10)
                    panoid = self.extract_panoid_from_url(url)
                    if not panoid:
                        raise Exception("Could not extract panoid from URL")
                    
                    self.send_log(f"Found panoid: {panoid}")
                    temp_dir = output_dir / panoid
                    
                    # Download
                    self.update_progress("Downloading tiles...", 20)
                    successful_tiles = self.download_streetview_tiles(panoid, temp_dir, zoom)
                    if successful_tiles == 0:
                        raise Exception("Download failed - no tiles downloaded")
                    
                    # Normalize
                    self.update_progress("Normalizing tiles...", 70)
                    self.normalize_tiles(temp_dir)
                    
                    # Stitch
                    self.update_progress("Stitching panorama...", 90)
                    self.stitch_tiles(temp_dir, output_dir, pano_name)
                    
                elif mode == "download":
                    panoid = self.extract_panoid_from_url(url)
                    if not panoid:
                        raise Exception("Could not extract panoid from URL")
                    
                    self.send_log(f"Found panoid: {panoid}")
                    temp_dir = output_dir / panoid
                    
                    successful_tiles = self.download_streetview_tiles(panoid, temp_dir, zoom)
                    if successful_tiles == 0:
                        raise Exception("Download failed - no tiles downloaded")
                
                # Handle normalize/stitch only modes for Street View
                elif mode in ["normalize", "stitch"]:
                    # For these modes, treat URL as panoid if not a URL
                    if url.startswith("http"):
                        panoid = self.extract_panoid_from_url(url)
                        if not panoid:
                            raise Exception("Could not extract panoid from URL")
                    else:
                        panoid = url
                    
                    temp_dir = output_dir / panoid
                    if not temp_dir.exists():
                        raise Exception(f"Directory {panoid} does not exist in {output_dir}")
                    
                    if mode == "normalize":
                        self.normalize_tiles(temp_dir)
                    elif mode == "stitch":
                        self.stitch_tiles(temp_dir, output_dir, pano_name)
            
            else:
                # Template URL workflow
                if mode == "full":
                    # Extract info and create temp directory
                    self.update_progress("Analyzing template...", 10)
                    folder_name, zoom = self.extract_info_from_template(url)
                    temp_dir = output_dir / folder_name
                    
                    # Download
                    self.update_progress("Downloading tiles...", 20)
                    successful_tiles = self.download_template_tiles(url, temp_dir, folder_name, zoom)
                    if successful_tiles == 0:
                        raise Exception("Download failed - no tiles downloaded")
                    
                    # Normalize
                    self.update_progress("Normalizing tiles...", 70)
                    self.normalize_tiles(temp_dir)
                    
                    # Stitch
                    self.update_progress("Stitching panorama...", 90)
                    self.stitch_tiles(temp_dir, output_dir, pano_name)
                
                elif mode == "download":
                    folder_name, zoom = self.extract_info_from_template(url)
                    temp_dir = output_dir / folder_name
                    
                    successful_tiles = self.download_template_tiles(url, temp_dir, folder_name, zoom)
                    if successful_tiles == 0:
                        raise Exception("Download failed - no tiles downloaded")
                
                # Handle normalize/stitch only modes for template
                elif mode in ["normalize", "stitch"]:
                    # For these modes, use the pano_name as folder name
                    temp_dir = output_dir / pano_name
                    if not temp_dir.exists():
                        raise Exception(f"Directory {pano_name} does not exist in {output_dir}")
                    
                    if mode == "normalize":
                        self.normalize_tiles(temp_dir)
                    elif mode == "stitch":
                        self.stitch_tiles(temp_dir, output_dir, pano_name)
            
            # Clean up tiles if requested and we did stitching
            if args['delete_tiles'] and mode in ["full", "stitch"] and temp_dir and temp_dir.exists():
                self.update_progress("Cleaning up tiles...", 95)
                self.send_log("Deleting tile folder...")
                shutil.rmtree(temp_dir)
                self.send_log("Tile folder deleted")
            
            self.update_progress("Complete!", 100)
            self.send_log("Operation completed successfully!")
            
            # Open folder if requested
            if args['open_folder']:
                self.open_folder(str(output_dir))
                
        except Exception as e:
            self.send_log(f"ERROR: {str(e)}")
            self.update_progress("Failed", 0)
        
        finally:
            self.progress_queue.put(("finished", None))
    
    def extract_panoid_from_url(self, url):
        """Extract panoid from Street View URL."""
        # Look for panoid in the URL data parameter
        match = re.search(r'panoid%3D([A-Za-z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        # Alternative pattern for unencoded URLs
        match = re.search(r'panoid=([A-Za-z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        # Look for panoid in the main part of the URL (format: 1s<panoid>)
        match = re.search(r'1s([A-Za-z0-9_-]+)', url)
        if match:
            return match.group(1)
        
        return None
    
    def extract_info_from_template(self, template_url):
        """Extract information from template URL."""
        # Extract zoom level
        zoom_match = re.search(r'-z(\d+)', template_url)
        zoom = int(zoom_match.group(1)) if zoom_match else 5
        
        # Create a unique identifier from the template
        if 'googleapis.com' in template_url:
            match = re.search(r'gps-cs-s/([^=]+)', template_url)
            if match:
                base_part = match.group(1)
                folder_name = f"photosphere_{base_part[:20]}"
            else:
                folder_name = f"photosphere_zoom{zoom}"
        else:
            folder_name = f"tiles_zoom{zoom}"
        
        return folder_name, zoom
    
    def download_streetview_tiles(self, panoid, temp_dir, zoom):
        """Download Street View tiles."""
        temp_dir.mkdir(exist_ok=True)
        
        if zoom is None:
            zoom = 5  # Start with zoom 5
        
        # Try specified zoom
        self.send_log(f"Attempting download at zoom {zoom}")
        successful_tiles = self.attempt_streetview_download_at_zoom(panoid, temp_dir, zoom)
        
        # Fallback to zoom 4 if zoom 5 failed
        if zoom == 5 and successful_tiles < 10:
            self.send_log("Zoom 5 download failed - falling back to zoom 4")
            zoom = 4
            successful_tiles = self.attempt_streetview_download_at_zoom(panoid, temp_dir, zoom)
        
        return successful_tiles
    
    def attempt_streetview_download_at_zoom(self, panoid, temp_dir, zoom):
        """Attempt to download Street View tiles at specific zoom."""
        width = 2 ** (zoom + 1)
        height = 2 ** zoom
        total_tiles = width * height
        
        self.send_log(f"Grid size: {width}x{height} ({total_tiles} tiles)")
        
        successful = 0
        failed = 0
        
        for x in range(width):
            for y in range(height):
                filename = f"{panoid}_x{x}-y{y}-zoom{zoom}-nbt1-fover2.jpg"
                filepath = temp_dir / filename
                
                if filepath.exists():
                    successful += 1
                    continue
                
                url = f"https://streetviewpixels-pa.googleapis.com/v1/tile?cb_client=maps_sv.tactile&panoid={panoid}&x={x}&y={y}&zoom={zoom}&nbt=1&fover=2"
                
                if self.download_image(url, filepath):
                    successful += 1
                else:
                    failed += 1
                    if filepath.exists():
                        filepath.unlink()
                
                # Early termination check
                total_attempted = successful + failed
                if total_attempted >= 50 and successful < 5:
                    self.send_log(f"Low success rate after {total_attempted} attempts - stopping")
                    break
            
            if total_attempted >= 50 and successful < 5:
                break
        
        success_rate = successful / max(1, successful + failed) * 100
        self.send_log(f"Zoom {zoom}: {successful} successful, {failed} failed ({success_rate:.1f}% success)")
        
        return successful
    
    def download_template_tiles(self, template_url, temp_dir, folder_name, zoom):
        """Download tiles using template URL."""
        temp_dir.mkdir(exist_ok=True)
        
        # Find grid boundaries
        max_x, max_y = self.find_grid_boundaries(template_url)
        total_tiles = max_x * max_y
        
        self.send_log(f"Will attempt to download {total_tiles} tiles...")
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        for x in range(max_x):
            for y in range(max_y):
                # Replace placeholders
                url = template_url.replace('[%X]', str(x)).replace('[%Y]', str(y))
                
                # Create filename
                filename = f"{folder_name}_x{x}-y{y}-zoom{zoom}.jpg"
                filepath = temp_dir / filename
                
                # Skip if exists
                if filepath.exists():
                    successful += 1
                    continue
                
                # Download
                if self.download_image(url, filepath):
                    successful += 1
                    if successful % 10 == 0:  # Progress every 10 tiles
                        elapsed = time.time() - start_time
                        rate = successful / elapsed if elapsed > 0 else 0
                        self.send_log(f"  Progress: {successful}/{total_tiles} tiles ({rate:.1f} tiles/sec)")
                else:
                    failed += 1
                    if filepath.exists():
                        filepath.unlink()
        
        self.send_log(f"Download complete! Successful: {successful}, Failed: {failed}")
        success_rate = successful / (successful + failed) * 100 if (successful + failed) > 0 else 0
        self.send_log(f"Success rate: {success_rate:.1f}%")
        
        return successful
    
    def find_grid_boundaries(self, template_url):
        """Find the actual grid boundaries by testing tiles."""
        self.send_log("Finding grid boundaries...")
        
        # Extract zoom level for search range
        zoom_match = re.search(r'-z(\d+)', template_url)
        zoom = int(zoom_match.group(1)) if zoom_match else 5
        
        if zoom == 5:
            max_x_search = 64
            max_y_search = 32
        elif zoom == 4:
            max_x_search = 32
            max_y_search = 16
        else:
            max_x_search = 2 ** (zoom + 1)
            max_y_search = 2 ** zoom
        
        self.send_log(f"Searching grid up to {max_x_search}x{max_y_search} for zoom {zoom}")
        
        max_x_found = 0
        max_y_found = 0
        
        # Test X boundary
        self.send_log("Testing X boundary...")
        for x in range(0, max_x_search, 4):  # Test every 4th position
            test_url = template_url.replace('[%X]', str(x)).replace('[%Y]', '0')
            if self.test_tile_exists(test_url):
                max_x_found = x
                self.send_log(f"  Found tile at x={x}")
        
        # Test around found boundary more precisely
        for x in range(max(0, max_x_found - 8), min(max_x_search, max_x_found + 16)):
            test_url = template_url.replace('[%X]', str(x)).replace('[%Y]', '0')
            if self.test_tile_exists(test_url):
                max_x_found = max(max_x_found, x)
        
        # Test Y boundary
        self.send_log("Testing Y boundary...")
        for y in range(0, max_y_search, 2):  # Test every 2nd position
            test_url = template_url.replace('[%X]', '0').replace('[%Y]', str(y))
            if self.test_tile_exists(test_url):
                max_y_found = y
                self.send_log(f"  Found tile at y={y}")
        
        # Test around found Y boundary
        for y in range(max(0, max_y_found - 4), min(max_y_search, max_y_found + 8)):
            test_url = template_url.replace('[%X]', '0').replace('[%Y]', str(y))
            if self.test_tile_exists(test_url):
                max_y_found = max(max_y_found, y)
        
        # Use full theoretical bounds if detection seems too small
        theoretical_tiles = max_x_search * max_y_search
        detected_tiles = (max_x_found + 1) * (max_y_found + 1)
        
        if detected_tiles < theoretical_tiles * 0.1:  # Less than 10% of theoretical
            self.send_log(f"Detection found only {detected_tiles} tiles vs {theoretical_tiles} theoretical")
            self.send_log("Using full theoretical bounds instead")
            max_x_found = max_x_search - 1
            max_y_found = max_y_search - 1
        
        actual_width = max_x_found + 1
        actual_height = max_y_found + 1
        
        self.send_log(f"Final grid boundaries: {actual_width}x{actual_height} ({actual_width * actual_height} tiles)")
        return actual_width, actual_height
    
    def test_tile_exists(self, url):
        """Test if a tile URL returns a valid image."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.head(url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def download_image(self, url, filename):
        """Download an image from URL and save it."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('image/'):
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False
                
        except requests.RequestException:
            return False
    
    def normalize_tiles(self, tile_dir):
        """Normalize tiles to consistent size."""
        self.send_log("Normalizing tile sizes...")
        
        # Find all tile sizes
        sizes = {}
        largest_size = (0, 0)
        
        for file_path in tile_dir.glob("*.jpg"):
            try:
                with Image.open(file_path) as img:
                    size = img.size
                    if size not in sizes:
                        sizes[size] = 0
                    sizes[size] += 1
                    
                    if size[0] * size[1] > largest_size[0] * largest_size[1]:
                        largest_size = size
            except:
                continue
        
        if not sizes:
            raise Exception("No tiles found to normalize")
        
        self.send_log("Tile size distribution:")
        for size, count in sorted(sizes.items()):
            self.send_log(f"  {size[0]}x{size[1]}: {count} tiles")
        
        self.send_log(f"Normalizing all tiles to: {largest_size[0]}x{largest_size[1]}")
        
        # Resize tiles if needed
        resized_count = 0
        for file_path in tile_dir.glob("*.jpg"):
            try:
                img = Image.open(file_path)
                if img.size != largest_size:
                    img_resized = img.resize(largest_size, Image.Resampling.LANCZOS)
                    img_resized.save(file_path, 'JPEG', quality=95)
                    resized_count += 1
                img.close()
            except Exception as e:
                self.send_log(f"Error resizing {file_path.name}: {e}")
        
        self.send_log(f"Resized {resized_count} tiles")
    
    def stitch_tiles(self, tile_dir, output_dir, pano_name):
        """Stitch tiles into a panorama."""
        self.send_log("Stitching panorama...")
        
        # Find zoom level and load tiles
        tiles = []
        zoom = None
        
        for file_path in tile_dir.glob("*.jpg"):
            # Extract coordinates and zoom from filename
            match = re.search(r'x(\d+)-y(\d+)-zoom(\d+)', file_path.name)
            if match:
                x, y, z = int(match.group(1)), int(match.group(2)), int(match.group(3))
                if zoom is None:
                    zoom = z
                
                try:
                    img = Image.open(file_path)
                    tiles.append({
                        'image': img,
                        'x': x,
                        'y': y,
                        'filename': file_path.name
                    })
                except Exception as e:
                    self.send_log(f"Error loading {file_path.name}: {e}")
        
        if not tiles:
            raise Exception("No tiles found for stitching")
        
        self.send_log(f"Found {len(tiles)} tiles for zoom {zoom}")
        
        # Calculate canvas size
        tile_width, tile_height = tiles[0]['image'].size
        max_x = max(tile['x'] for tile in tiles)
        max_y = max(tile['y'] for tile in tiles)
        
        canvas_width = (max_x + 1) * tile_width
        canvas_height = (max_y + 1) * tile_height
        
        self.send_log(f"Canvas size: {canvas_width}x{canvas_height}")
        self.send_log(f"Tile size: {tile_width}x{tile_height}")
        
        # Create canvas
        canvas = Image.new('RGB', (canvas_width, canvas_height), (0, 0, 0))
        
        # Place tiles
        placed = 0
        for tile in tiles:
            x_pos = tile['x'] * tile_width
            y_pos = tile['y'] * tile_height
            
            if x_pos + tile_width <= canvas_width and y_pos + tile_height <= canvas_height:
                canvas.paste(tile['image'], (x_pos, y_pos))
                placed += 1
        
        # Crop to 2:1 aspect ratio (remove bottom black bars)
        target_height = canvas_width // 2
        if canvas_height > target_height:
            # Crop from the bottom
            canvas = canvas.crop((0, 0, canvas_width, target_height))
            self.send_log(f"Cropped from {canvas_width}x{canvas_height} to {canvas_width}x{target_height} (2:1 ratio)")
        elif canvas_height < target_height:
            # If somehow too short, expand with black at bottom (shouldn't happen normally)
            new_canvas = Image.new('RGB', (canvas_width, target_height), (0, 0, 0))
            new_canvas.paste(canvas, (0, 0))
            canvas = new_canvas
            self.send_log(f"Expanded from {canvas_width}x{canvas_height} to {canvas_width}x{target_height} (2:1 ratio)")
        else:
            self.send_log(f"Canvas already at perfect 2:1 ratio: {canvas_width}x{canvas_height}")
        
        # Save panorama
        output_filename = f"{pano_name}_panorama.jpg"
        output_path = Path(output_dir) / output_filename
        
        canvas.save(output_path, 'JPEG', quality=95)
        
        self.send_log(f"Placed {placed} tiles")
        self.send_log(f"Final panorama size: {canvas.width}x{canvas.height} (2:1 ratio)")
        self.send_log(f"Panorama saved as: {output_path}")
        
        # Close images
        for tile in tiles:
            tile['image'].close()
    
    def update_progress(self, status, progress):
        self.progress_queue.put(("progress", (status, progress)))
    
    def send_log(self, message):
        self.progress_queue.put(("log", message))
    
    def open_folder(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.run(["open", path])
            else:
                subprocess.run(["xdg-open", path])
        except:
            pass
    
    def start_progress_monitor(self):
        # Update timer if running
        if self.is_running and self.start_time:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.timer_var.set(f"Running: {minutes:02d}:{seconds:02d}")
        elif not self.is_running:
            self.timer_var.set("")
        
        try:
            while True:
                msg_type, data = self.progress_queue.get_nowait()
                
                if msg_type == "progress":
                    status, progress = data
                    self.status_var.set(f"Status: {status}")
                    self.progress_var.set(progress)
                elif msg_type == "log":
                    self.log(data)
                elif msg_type == "finished":
                    self.is_running = False
                    self.start_button.config(text="Start Download", state="normal")
                    self.timer_var.set("")
                    break
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.start_progress_monitor)
    
    def show_help(self):
        help_text = """Unified Panorama Downloader Help

URL Types:
• Street View: Paste a Google Maps Street View URL
• Template: Use custom URLs with [%X] and [%Y] placeholders
  Example: https://example.com/tile?x=[%X]&y=[%Y]&z=5

Panorama Name:
• Will be used as filename: [name]_panorama.jpg
• Default uses timestamp format: YYYYMMDDHHMMSS

Modes:
• Full Pipeline: Download → Normalize → Stitch
• Download Only: Just download tiles
• Normalize Only: Resize existing tiles to consistent size
• Stitch Only: Combine existing tiles into panorama

Options:
• Auto Zoom: Tries zoom 5, falls back to zoom 4 (Street View only)
• Delete Tiles: Removes tile folder after successful stitching
• Open Folder: Opens result folder when complete

The program handles mixed tile sizes and creates high-quality panoramas.
"""
        messagebox.showinfo("Help", help_text)
    
    def show_about(self):
        about_text = """Unified Panorama Downloader v1.0

Downloads and stitches panoramas from:
• Google Street View URLs
• Custom template URLs with coordinate placeholders

Features:
• Automatic zoom detection and fallback
• Mixed tile size normalization
• High-quality panorama generation
• Conflict detection and resolution
• Automatic cleanup options

Created for panorama enthusiasts.
"""
        messagebox.showinfo("About", about_text)


def main():
    root = tk.Tk()
    app = PanoramaDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
                        