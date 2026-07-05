import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import feedparser
import re
from datetime import datetime
import webbrowser


class InfoCollector:
    def __init__(self, root):
        self.root = root
        self.root.title("сбор новостной информации")
        self.root.geometry("800x700")

        self.keywords_var = tk.StringVar()
        self.sources = {
            "РИА Новости": "https://ria.ru/export/rss2/index.xml",
            "ТАСС": "https://tass.ru/rss/v2.xml",
            "Интерфакс": "https://www.interfax.ru/rss.asp",
            "Lenta.ru": "https://lenta.ru/rss",
            "РБК": "https://www.rbc.ru/rss/news",
            "Коммерсантъ": "https://www.kommersant.ru/RSS/news.xml",
            "Ведомости": "https://www.vedomosti.ru/rss/news",
            "Известия": "https://iz.ru/xml/rss/all.xml",
        }
        self.source_vars = {src: tk.BooleanVar(value=True) for src in self.sources}
        self.results = []

        top_frame = ttk.Frame(root)
        top_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(top_frame, text="Ключевые слова:").grid(row=0, column=0, sticky=tk.W)
        self.keywords_entry = ttk.Entry(top_frame, textvariable=self.keywords_var, width=40)
        self.keywords_entry.grid(row=0, column=1, padx=5, sticky=tk.W)

        self.collect_btn = ttk.Button(top_frame, text="Собрать информацию", command=self.start_collect)
        self.collect_btn.grid(row=0, column=2, padx=5)

        self.clear_btn = ttk.Button(top_frame, text="Очистить", command=self.clear_results)
        self.clear_btn.grid(row=0, column=3, padx=5)

        sources_frame = ttk.LabelFrame(root, text="Источники", padding=5)
        sources_frame.pack(pady=5, padx=10)

        row, col = 0, 0
        for src in self.sources:
            cb = ttk.Checkbutton(sources_frame, text=src, variable=self.source_vars[src])
            cb.grid(row=row, column=col, sticky=tk.W, padx=5)
            col += 1
            if col > 3:
                col = 0
                row += 1

        output_frame = ttk.LabelFrame(root, text="Результаты", padding=5)
        output_frame.pack(pady=5, padx=3, fill=tk.BOTH, expand=True)

        self.output_text = scrolledtext.ScrolledText(output_frame, wrap=tk.WORD, font=("Times New Roman", 11))
        self.output_text.pack(fill=tk.BOTH, expand=True)


    def start_collect(self):
        self.results = []
        self.output_text.delete(1.0, tk.END)
        self.collect_btn.config(state=tk.NORMAL)

        keywords = self.keywords_var.get().strip()
        if not keywords:
            messagebox.showwarning("Предупреждение", "Введите ключевые слова.")
            return

        selected = []
        for src, var in self.source_vars.items():
            if var.get() == True:
                selected.append(src)

        self.collect_btn.config(state=tk.DISABLED)

        thread = threading.Thread(target=self.collect_info, args=(keywords, selected))
        thread.daemon = True
        thread.start()

    def collect_info(self, keywords_str, selected_sources):
        keywords = []
        temp_list = keywords_str.split(',')
        for kw in temp_list:
            clean_kw = kw.strip()
            if clean_kw:
                keywords.append(clean_kw.lower())

        self.results = []
        total = len(selected_sources)
        processed = 0

        for src_name in selected_sources:
            url = self.sources[src_name]
            try:
                feed = feedparser.parse(url)
                if feed.bozo:
                    continue
                for entry in feed.entries:
                    title = entry.get('title', '')
                    description = entry.get('description', '')
                    description = re.sub(r'<[^>]+>', '', description)
                    text = (title + ' ' + description).lower()
                    if any(kw in text for kw in keywords):
                        link = entry.get('link', '')
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            dt = datetime(*entry.published_parsed[:6])
                            date_str = dt.strftime('%d.%m.%Y %H:%M')
                        self.results.append((title, link, date_str, src_name))
            except Exception as e:
                pass

            processed += 1

        self.root.after(0, self.display_results)
        self.root.after(0, self.finish_collect)

    def display_results(self):
        self.output_text.delete(1.0, tk.END)
        if not self.results:
            self.output_text.insert(tk.END, "По вашему запросу ничего не найдено.")
            return
        self.output_text.tag_configure("link", foreground="blue")
        self.output_text.tag_bind("link", "<Button-1>", self.open_link)

        for i, (title, link, date, source) in enumerate(self.results, 1):
            self.output_text.insert(tk.END, f"{i}. {title}\n", 'title')
            self.output_text.insert(tk.END, f"   Источник: {source}\n")
            self.output_text.insert(tk.END, f"   Дата: {date}\n")
            self.output_text.insert(tk.END, f"   Ссылка: {link}\n\n", 'link')

            start_pos = self.output_text.index(tk.END)
            end_pos = self.output_text.index(tk.END)

            self.output_text.tag_add("link", start_pos, end_pos)

    def open_link(self, event):
        index = self.output_text.index(f"@{event.x},{event.y}")
        tags = self.output_text.tag_names(index)
        if "link" in tags:
            line_start = self.output_text.index(f"{index} linestart")
            line_end = self.output_text.index(f"{index} lineend")
            line_text = self.output_text.get(line_start, line_end)
            if "Ссылка: " in line_text:
                link = line_text.split("Ссылка: ", 1)[1].strip()
                webbrowser.open(link)


    def finish_collect(self):
        self.collect_btn.config(state=tk.NORMAL)

    def clear_results(self):
        self.output_text.delete(1.0, tk.END)
        self.results.clear()
        self.collect_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = InfoCollector(root)
    root.mainloop()