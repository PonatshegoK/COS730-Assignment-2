from tkinter import filedialog, Frame, Canvas, Tk, messagebox, Menu, BooleanVar, Toplevel, Listbox
from tkinter.ttk import Scrollbar
import fitz
from PIL import Image, ImageTk
import io
import pyttsx3
import tkinter as tk


class EbookReader:
    def __init__(self, root):
        self.root = root
        self.root.title("Ebook Reader")
        self.root.geometry("650x800")
        self.root.configure(bg="white")
        
      
        menubar = Menu(root)
        root.config(menu=menubar)

        
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.browse_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        
        view_menu = Menu(menubar, tearoff=0)
        self.speech_to_text_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label="Turn on speech to text", variable=self.speech_to_text_var, command=self.toggle_tts)
        menubar.add_cascade(label="View", menu=view_menu)

       
        highlight_menu = Menu(menubar, tearoff=0)
        highlight_menu.add_command(label="Highlight Text", command=self.highlight_text)
        menubar.add_cascade(label="Highlight", menu=highlight_menu)

        
        bookmarks_menu = Menu(menubar, tearoff=0)
        bookmarks_menu.add_command(label="Add Bookmark", command=self.add_bookmark)
        bookmarks_menu.add_command(label="View Bookmarks", command=self.view_bookmarks)
        menubar.add_cascade(label="Bookmarks", menu=bookmarks_menu)

      
        self.canvas_frame = tk.Frame(root, bg="white")
        self.canvas_frame.pack(fill="both", expand=True)

  
        self.canvas = tk.Canvas(self.canvas_frame, bg="white", cursor="arrow")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.v_scroll = Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.v_scroll.pack(side="right", fill="y")
        self.h_scroll = Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.h_scroll.pack(side="bottom", fill="x")
        self.canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)

       
        self.tts_engine = pyttsx3.init()

     
        self.ebook = None
        self.current_page = 0
        self.zoom_level = 1.0

        self.highlights = {}
        self.bookmarks = {}

       
        self.canvas.bind("<MouseWheel>", self.scroll_page)

        
        self.selection_start = None
        self.selection_end = None

    def browse_file(self):
        filename = filedialog.askopenfilename(initialdir=".", 
                                              title="Select Ebook file", 
                                              filetypes=[("PDF files", "*.pdf"),
                                                         ("EPUB files", "*.epub"),
                                                         ("MOBI files", "*.mobi")])
        if filename:
            self.load_ebook(filename)

    def load_ebook(self, filename):
        self.ebook = fitz.open(filename)
        self.current_page = 0
        self.show_page(self.current_page)

    def show_page(self, page_num):
        if self.ebook:
            page = self.ebook.load_page(page_num)
            zoom_matrix = fitz.Matrix(self.zoom_level, self.zoom_level)
            pix = page.get_pixmap(matrix=zoom_matrix)
            width, height = pix.width, pix.height
            img = Image.open(io.BytesIO(pix.tobytes()))
            img = ImageTk.PhotoImage(img)

            self.canvas.delete("all")  
            self.canvas.config(scrollregion=(0, 0, width, height))
            self.canvas.create_image(0, 0, anchor="nw", image=img)
            self.canvas.image = img  
            self.root.update_idletasks()
            self.canvas.yview_moveto(0)

           
            if page_num in self.highlights:
                for highlight in self.highlights[page_num]:
                    self.canvas.create_rectangle(highlight, outline="", fill="yellow", stipple="gray50")

            
            if self.speech_to_text_var.get():
                text = page.get_text("text")
                self.read_aloud(text)

    def scroll_page(self, event):
        if self.ebook:
            if event.delta < 0:
                self.next_page()
            else:
                self.previous_page()

    def previous_page(self):
        if self.ebook and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def next_page(self):
        if self.ebook and self.current_page < len(self.ebook) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def read_aloud(self, text):
        if self.speech_to_text_var.get():
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()

    def read_selected_text(self):
        if not self.ebook or not self.selection_start or not self.selection_end:
            return

        
        page = self.ebook.load_page(self.current_page)
        rect = fitz.Rect(self.selection_start[0], self.selection_start[1], self.selection_end[0], self.selection_end[1])
        selected_text = page.get_textbox(rect)
        self.read_aloud(selected_text)

    def highlight_text(self):
        
        if self.highlight_var.get():
            self.canvas.bind("<Button-1>", self.start_selection)
            self.canvas.bind("<B1-Motion>", self.update_selection)
            self.canvas.bind("<ButtonRelease-1>", self.end_selection)
        else:
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")
            self.canvas.delete("highlight")

    def start_selection(self, event):
        
        self.selection_start = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))

    def update_selection(self, event):
        
        self.selection_end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        self.draw_highlight_rectangle()

    def end_selection(self, event):
        if not self.ebook:
            return

        self.selection_end = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        rect = (self.selection_start[0], self.selection_start[1], self.selection_end[0], self.selection_end[1])

        if self.current_page not in self.highlights:
            self.highlights[self.current_page] = []
        self.highlights[self.current_page].append(rect)

        self.canvas.delete("highlight")
        self.canvas.create_rectangle(rect, outline="", fill="yellow", stipple="gray50")
    def draw_highlight_rectangle(self):
       
        self.canvas.delete("highlight")

        if self.selection_start and self.selection_end:
            
            x0, y0 = self.selection_start
            x1, y1 = self.selection_end
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="", fill="yellow", stipple="gray50", tags="highlight")

    def add_bookmark(self):
        if not self.ebook:
            return
        if self.current_page not in self.bookmarks:
            self.bookmarks[self.current_page] = f"Page {self.current_page + 1}"
            messagebox.showinfo("Bookmark Added", f"Bookmark added for page {self.current_page + 1}")
        else:
            messagebox.showinfo("Bookmark Exists", f"Bookmark already exists for page {self.current_page + 1}")

    def view_bookmarks(self):
        if not self.bookmarks:
            messagebox.showinfo("No Bookmarks", "No bookmarks have been added.")
            return
        
        bookmarks_window = tk.Toplevel(self.root)
        bookmarks_window.title("Bookmarks")
        bookmarks_window.geometry("300x400")
        
        listbox = tk.Listbox(bookmarks_window)
        listbox.pack(fill="both", expand=True)
        
        for page_num, title in self.bookmarks.items():
            listbox.insert("end", f"{title}")

        def go_to_bookmark(event):
            selected = listbox.curselection()
            if selected:
                bookmark = listbox.get(selected)
                page_num = int(bookmark.split()[-1]) - 1
                self.current_page = page_num
                self.show_page(self.current_page)
                bookmarks_window.destroy()
        
        listbox.bind("<Double-Button-1>", go_to_bookmark)

    def toggle_tts(self):
        if self.speech_to_text_var.get():
            messagebox.showinfo("TTS Enabled", "Text-to-Speech has been enabled.")
        else:
            self.tts_engine.stop()
            messagebox.showinfo("TTS Disabled", "Text-to-Speech has been disabled.") 