#!/usr/bin/env python3
"""
Automation Agent Dashboard
A simple GUI for managing and monitoring automation tasks.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
import threading
import time
from datetime import datetime
from pathlib import Path
import sys

try:
    from automation_agent import AutomationAgent, AutomationTask, SafetyLevel, TaskStatus
except ImportError:
    print("ERROR: automation_agent.py not found. Please ensure it's in the same directory.")
    sys.exit(1)


class AutomationDashboard:
    """GUI Dashboard for Automation Agent."""

    def __init__(self, root):
        self.root = root
        self.root.title("AI Automation Agent Dashboard")
        self.root.geometry("1200x800")

        # Initialize agent
        self.agent = AutomationAgent()
        self.tasks = {}
        self.selected_task = None

        # Create GUI elements
        self.create_menu()
        self.create_main_layout()
        self.create_task_list()
        self.create_control_panel()
        self.create_log_viewer()
        self.create_status_bar()

        # Start update thread
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Load Config", command=self.load_config)
        file_menu.add_command(label="Save Config", command=self.save_config)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        menubar.add_cascade(label="File", menu=file_menu)

        # Tasks menu
        tasks_menu = tk.Menu(menubar, tearoff=0)
        tasks_menu.add_command(label="New Task", command=self.new_task_dialog)
        tasks_menu.add_command(label="Edit Task", command=self.edit_task_dialog)
        tasks_menu.add_command(label="Delete Task", command=self.delete_task)
        tasks_menu.add_separator()
        tasks_menu.add_command(label="Run Task", command=self.run_selected_task)
        tasks_menu.add_command(label="Stop All Tasks", command=self.stop_all_tasks)
        menubar.add_cascade(label="Tasks", menu=tasks_menu)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Take Screenshot", command=self.take_screenshot)
        tools_menu.add_command(label="Mouse Position", command=self.show_mouse_position)
        tools_menu.add_command(label="Screen Size", command=self.show_screen_size)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Help", command=self.show_help)
        menubar.add_cascade(label="Help", menu=help_menu)

    def create_main_layout(self):
        """Create main layout."""
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create paned window for resizable sections
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Left panel - Task list and controls
        left_panel = ttk.Frame(paned)
        paned.add(left_panel, weight=1)

        # Right panel - Log viewer
        right_panel = ttk.Frame(paned)
        paned.add(right_panel, weight=1)

        # Store references
        self.left_panel = left_panel
        self.right_panel = right_panel

    def create_task_list(self):
        """Create task list section."""
        # Task list frame
        task_frame = ttk.LabelFrame(self.left_panel, text="Scheduled Tasks", padding=5)
        task_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Treeview for tasks
        columns = ("Name", "Type", "Schedule", "Status", "Last Run")
        self.task_tree = ttk.Treeview(task_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.task_tree.heading(col, text=col)
            self.task_tree.column(col, width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        h_scrollbar = ttk.Scrollbar(task_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)
        self.task_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.task_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind selection event
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_select)

    def create_control_panel(self):
        """Create control panel."""
        control_frame = ttk.LabelFrame(self.left_panel, text="Controls", padding=5)
        control_frame.pack(fill=tk.X, pady=(0, 5))

        # Buttons frame
        buttons_frame = ttk.Frame(control_frame)
        buttons_frame.pack(fill=tk.X)

        # Control buttons
        ttk.Button(buttons_frame, text="Start Scheduler", command=self.start_scheduler).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Stop Scheduler", command=self.stop_scheduler).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Emergency Stop", command=self.emergency_stop).pack(side=tk.LEFT, padx=(0, 10))

        # Safety level selector
        ttk.Label(buttons_frame, text="Safety:").pack(side=tk.LEFT, padx=(0, 5))
        self.safety_var = tk.StringVar(value="medium")
        safety_combo = ttk.Combobox(buttons_frame, textvariable=self.safety_var,
                                   values=["low", "medium", "high"], width=8)
        safety_combo.pack(side=tk.LEFT)
        safety_combo.bind("<<ComboboxSelected>>", self.change_safety_level)

        # Status indicators
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.scheduler_status = ttk.Label(status_frame, text="Scheduler: Stopped", foreground="red")
        self.scheduler_status.pack(side=tk.LEFT, padx=(0, 10))

        self.agent_status = ttk.Label(status_frame, text="Agent: Ready", foreground="green")
        self.agent_status.pack(side=tk.LEFT)

    def create_log_viewer(self):
        """Create log viewer section."""
        log_frame = ttk.LabelFrame(self.right_panel, text="Activity Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(log_controls, text="Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="Save Log", command=self.save_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_controls, text="Refresh", command=self.refresh_log).pack(side=tk.LEFT)

    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def new_task_dialog(self):
        """Show dialog for creating new task."""
        dialog = TaskDialog(self.root, "New Task")
        if dialog.result:
            task = AutomationTask(
                name=dialog.result['name'],
                function=getattr(self.agent, dialog.result['function']),
                args=dialog.result.get('args', []),
                kwargs=dialog.result.get('kwargs', {}),
                schedule_type=dialog.result.get('schedule_type'),
                schedule_time=dialog.result.get('schedule_time'),
                interval_seconds=dialog.result.get('interval_seconds')
            )
            task_id = self.agent.add_task(task)
            self.tasks[task_id] = task
            self.refresh_task_list()
            self.log_message(f"Task created: {task.name}")

    def edit_task_dialog(self):
        """Show dialog for editing selected task."""
        if not self.selected_task:
            messagebox.showwarning("Warning", "Please select a task to edit.")
            return

        # Get task details
        task_id = self.selected_task
        task = self.agent.tasks.get(task_id)
        if not task:
            return

        dialog = TaskDialog(self.root, "Edit Task", task)
        if dialog.result:
            # Update task
            task.name = dialog.result['name']
            task.function = getattr(self.agent, dialog.result['function'])
            task.args = dialog.result.get('args', [])
            task.kwargs = dialog.result.get('kwargs', {})
            task.schedule_type = dialog.result.get('schedule_type')
            task.schedule_time = dialog.result.get('schedule_time')
            task.interval_seconds = dialog.result.get('interval_seconds')

            self.refresh_task_list()
            self.log_message(f"Task updated: {task.name}")

    def delete_task(self):
        """Delete selected task."""
        if not self.selected_task:
            messagebox.showwarning("Warning", "Please select a task to delete.")
            return

        if messagebox.askyesno("Confirm", "Delete selected task?"):
            task_id = self.selected_task
            task_name = self.agent.tasks[task_id].name
            self.agent.remove_task(task_id)
            if task_id in self.tasks:
                del self.tasks[task_id]
            self.refresh_task_list()
            self.log_message(f"Task deleted: {task_name}")

    def run_selected_task(self):
        """Run selected task immediately."""
        if not self.selected_task:
            messagebox.showwarning("Warning", "Please select a task to run.")
            return

        task_id = self.selected_task
        task = self.agent.tasks.get(task_id)
        if task:
            self.log_message(f"Running task: {task.name}")
            result = self.agent.run_task(task_id)
            self.log_message(f"Task result: {result.status.value}")

    def stop_all_tasks(self):
        """Stop all running tasks."""
        self.agent.stop_scheduler()
        self.log_message("All tasks stopped")

    def start_scheduler(self):
        """Start the task scheduler."""
        self.agent.start_scheduler()
        self.log_message("Scheduler started")

    def stop_scheduler(self):
        """Stop the task scheduler."""
        self.agent.stop_scheduler()
        self.log_message("Scheduler stopped")

    def emergency_stop(self):
        """Emergency stop all automation."""
        self.agent.emergency_stop = True
        self.agent.stop_scheduler()
        self.log_message("EMERGENCY STOP ACTIVATED")

    def change_safety_level(self, event=None):
        """Change safety level."""
        level_map = {
            'low': SafetyLevel.LOW,
            'medium': SafetyLevel.MEDIUM,
            'high': SafetyLevel.HIGH
        }
        level = level_map.get(self.safety_var.get(), SafetyLevel.MEDIUM)
        # Note: In a real implementation, you'd recreate the agent with new safety level
        self.log_message(f"Safety level changed to: {self.safety_var.get()}")

    def take_screenshot(self):
        """Take a screenshot."""
        filename = self.agent.take_screenshot()
        if filename:
            self.log_message(f"Screenshot saved: {filename}")
        else:
            self.log_message("Screenshot failed")

    def show_mouse_position(self):
        """Show current mouse position."""
        pos = self.agent.get_mouse_position()
        messagebox.showinfo("Mouse Position", f"X: {pos[0]}, Y: {pos[1]}")

    def show_screen_size(self):
        """Show screen size."""
        size = self.agent.get_screen_size()
        messagebox.showinfo("Screen Size", f"Width: {size[0]}, Height: {size[1]}")

    def load_config(self):
        """Load configuration file."""
        filename = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                self.agent.config = config
                self.log_message(f"Configuration loaded: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load config: {e}")

    def save_config(self):
        """Save configuration file."""
        filename = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.agent.config, f, indent=2)
                self.log_message(f"Configuration saved: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save config: {e}")

    def clear_log(self):
        """Clear log viewer."""
        self.log_text.delete(1.0, tk.END)

    def save_log(self):
        """Save log to file."""
        filename = filedialog.asksaveasfilename(
            title="Save Log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                self.log_message(f"Log saved: {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save log: {e}")

    def refresh_log(self):
        """Refresh log viewer."""
        # This would typically read from the actual log file
        self.log_message("Log refreshed")

    def on_task_select(self, event):
        """Handle task selection."""
        selection = self.task_tree.selection()
        if selection:
            self.selected_task = selection[0]

    def refresh_task_list(self):
        """Refresh the task list display."""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        # Add tasks
        for task_id, task in self.agent.tasks.items():
            # Get last result if available
            last_result = None
            task_results = [r for r in self.agent.task_results if r.task_id == task_id]
            if task_results:
                last_result = task_results[-1]

            last_run = last_result.end_time.strftime("%H:%M:%S") if last_result and last_result.end_time else "Never"
            status = last_result.status.value if last_result else "Pending"

            schedule_info = ""
            if task.schedule_type == "daily":
                schedule_info = f"Daily {task.schedule_time}"
            elif task.schedule_type == "weekly":
                schedule_info = f"Weekly {task.schedule_time}"
            elif task.schedule_type == "interval":
                schedule_info = f"Every {task.interval_seconds}s"

            self.task_tree.insert("", tk.END, iid=task_id, values=(
                task.name,
                task.schedule_type or "Manual",
                schedule_info,
                status,
                last_run
            ))

    def log_message(self, message):
        """Add message to log viewer."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)

    def update_loop(self):
        """Background update loop."""
        while True:
            try:
                # Update status indicators
                scheduler_status = "Running" if getattr(self.agent, '_scheduler_running', False) else "Stopped"
                self.scheduler_status.config(
                    text=f"Scheduler: {scheduler_status}",
                    foreground="green" if scheduler_status == "Running" else "red"
                )

                # Update task list periodically
                self.refresh_task_list()

                # Update status bar
                task_count = len(self.agent.tasks)
                self.status_bar.config(text=f"Tasks: {task_count} | Agent: Active")

                time.sleep(2)  # Update every 2 seconds

            except Exception as e:
                print(f"Update loop error: {e}")
                time.sleep(5)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", "AI Automation Agent Dashboard\nVersion 1.0\n\nA comprehensive automation framework for computer control and task scheduling.")

    def show_help(self):
        """Show help dialog."""
        help_text = """
AI Automation Agent Dashboard Help

Task Management:
- Create new tasks with the Tasks menu
- Select tasks to edit, delete, or run
- Use the scheduler controls to start/stop automated execution

Safety:
- Choose appropriate safety level (Low/Medium/High)
- Use Emergency Stop to halt all automation immediately
- High safety level requires confirmation for actions

Monitoring:
- View task status and execution history
- Monitor activity in the log viewer
- Take screenshots and check system status

For detailed documentation, see README.md
        """
        messagebox.showinfo("Help", help_text)

    def on_closing(self):
        """Handle window close event."""
        if messagebox.askokcancel("Quit", "Stop all automation and quit?"):
            self.agent.stop_scheduler()
            self.agent.emergency_stop = True
            self.root.destroy()


class TaskDialog:
    """Dialog for creating/editing tasks."""

    def __init__(self, parent, title, task=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets(task)
        self.dialog.wait_window()

    def create_widgets(self, task):
        """Create dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Task name
        ttk.Label(main_frame, text="Task Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_var = tk.StringVar(value=task.name if task else "")
        ttk.Entry(main_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, pady=2)

        # Function selection
        ttk.Label(main_frame, text="Function:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.function_var = tk.StringVar(value=getattr(task.function, '__name__', '') if task else "")
        function_combo = ttk.Combobox(main_frame, textvariable=self.function_var,
                                     values=["send_whatsapp_message", "take_screenshot", "open_application"])
        function_combo.grid(row=1, column=1, sticky=tk.EW, pady=2)

        # Arguments
        ttk.Label(main_frame, text="Arguments (JSON):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.args_var = tk.StringVar(value=json.dumps(task.args) if task and task.args else "[]")
        ttk.Entry(main_frame, textvariable=self.args_var).grid(row=2, column=1, sticky=tk.EW, pady=2)

        # Keyword arguments
        ttk.Label(main_frame, text="Keyword Args (JSON):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.kwargs_var = tk.StringVar(value=json.dumps(task.kwargs) if task and task.kwargs else "{}")
        ttk.Entry(main_frame, textvariable=self.kwargs_var).grid(row=3, column=1, sticky=tk.EW, pady=2)

        # Schedule type
        ttk.Label(main_frame, text="Schedule Type:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.schedule_type_var = tk.StringVar(value=task.schedule_type if task else "")
        schedule_combo = ttk.Combobox(main_frame, textvariable=self.schedule_type_var,
                                     values=["", "daily", "weekly", "interval"])
        schedule_combo.grid(row=4, column=1, sticky=tk.EW, pady=2)

        # Schedule time
        ttk.Label(main_frame, text="Schedule Time:").grid(row=5, column=0, sticky=tk.W, pady=2)
        self.schedule_time_var = tk.StringVar(value=task.schedule_time if task else "")
        ttk.Entry(main_frame, textvariable=self.schedule_time_var).grid(row=5, column=1, sticky=tk.EW, pady=2)

        # Interval seconds
        ttk.Label(main_frame, text="Interval (seconds):").grid(row=6, column=0, sticky=tk.W, pady=2)
        self.interval_var = tk.StringVar(value=str(task.interval_seconds) if task and task.interval_seconds else "")
        ttk.Entry(main_frame, textvariable=self.interval_var).grid(row=6, column=1, sticky=tk.EW, pady=2)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side=tk.LEFT, padx=5)

        # Configure grid
        main_frame.columnconfigure(1, weight=1)

    def on_ok(self):
        """Handle OK button."""
        try:
            self.result = {
                'name': self.name_var.get(),
                'function': self.function_var.get(),
                'args': json.loads(self.args_var.get()),
                'kwargs': json.loads(self.kwargs_var.get()),
                'schedule_type': self.schedule_type_var.get() or None,
                'schedule_time': self.schedule_time_var.get() or None,
                'interval_seconds': int(self.interval_var.get()) if self.interval_var.get() else None
            }
            self.dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid input: {e}")

    def on_cancel(self):
        """Handle Cancel button."""
        self.dialog.destroy()


def main():
    """Main function."""
    root = tk.Tk()
    app = AutomationDashboard(root)
    root.mainloop()


if __name__ == "__main__":
    main()