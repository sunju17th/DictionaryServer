import socket
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json

# Cấu hình kết nối mặc định
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 5555

class DictionaryClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Từ điển Online")
        self.root.geometry("900x650")
        
        self.socket = None
        self.user_role = None
        self.username = None
        self.connected = False
        
        # Style cho giao diện đẹp hơn
        self.style = ttk.Style()
        self.style.theme_use('clam') # Hoặc 'alt', 'default'
        
        self.setup_login_ui()
        
    def setup_login_ui(self):
        """Giao diện đăng nhập"""
        # Xóa main_frame cũ nếu tồn tại (khi logout)
        if hasattr(self, 'main_frame') and self.main_frame:
            self.main_frame.destroy()
        
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tiêu đề
        ttk.Label(self.main_frame, text="ĐĂNG NHẬP HỆ THỐNG", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Form nhập liệu
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack()
        
        ttk.Label(form_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_entry = ttk.Entry(form_frame, width=25)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_entry = ttk.Entry(form_frame, width=25)
        self.user_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pass_entry = ttk.Entry(form_frame, show="*", width=25)
        self.pass_entry.grid(row=2, column=1, pady=5)
        
        ttk.Button(form_frame, text="Kết nối & Đăng nhập", command=self.connect_and_login).grid(row=3, column=0, columnspan=2, pady=20)
        
        self.status_lbl = ttk.Label(self.main_frame, text="Chưa kết nối", foreground="gray")
        self.status_lbl.pack(side=tk.BOTTOM, pady=10)

    def setup_dashboard_ui(self):
        """Giao diện chính sau khi đăng nhập (Dùng Tabs)"""
        # Xóa giao diện login
        for widget in self.main_frame.winfo_children():
            widget.destroy()
            
        # Header chào mừng
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text=f"Xin chào, {self.username} ({self.user_role})", font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Đăng xuất", command=self.logout).pack(side=tk.RIGHT)

        # Tạo Tab Control
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # --- TAB 1: TRA CỨU ---
        self.tab_search = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_search, text=" Tra Cứu")
        self.build_search_tab()

        # --- TAB 2: DANH SÁCH TỪ (A-Z) ---
        self.tab_list = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_list, text=" Danh Sách Từ")
        self.build_list_tab()

        # --- TAB 3: ĐÓNG GÓP ---
        self.tab_contribute = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.tab_contribute, text=" Đóng Góp")
        self.build_contribute_tab()

        # --- TAB 4: ADMIN (Chỉ hiện nếu là admin) ---
        if self.user_role == 'admin':
            self.tab_admin = ttk.Frame(self.notebook, padding=10)
            self.notebook.add(self.tab_admin, text=" Quản trị (Admin)")
            self.build_admin_tab()

    # --- CÁC HÀM XÂY DỰNG GIAO DIỆN CON ---

    def build_search_tab(self):
        input_frame = ttk.Frame(self.tab_search)
        input_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(input_frame, text="Nhập từ cần tra:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(input_frame, width=40, font=("Arial", 11))
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.do_lookup()) # Enter để tìm
        
        ttk.Button(input_frame, text="Tìm kiếm", command=self.do_lookup).pack(side=tk.LEFT, padx=5)
        
        self.result_area = scrolledtext.ScrolledText(self.tab_search, height=15, font=("Arial", 11))
        self.result_area.pack(fill=tk.BOTH, expand=True, pady=10)
        self.result_area.tag_config('success', foreground='green')
        self.result_area.tag_config('error', foreground='red')

    def build_list_tab(self):
        # Nút làm mới
        ttk.Button(self.tab_list, text=" Làm mới danh sách", command=self.load_dictionary_list).pack(anchor=tk.W, pady=(0, 5))
        
        # Bảng Treeview
        columns = ("word", "meaning")
        self.tree_dict = ttk.Treeview(self.tab_list, columns=columns, show="headings", height=20)
        self.tree_dict.heading("word", text="Từ vựng")
        self.tree_dict.heading("meaning", text="Định nghĩa")
        self.tree_dict.column("word", width=200, anchor=tk.W)
        self.tree_dict.column("meaning", width=500, anchor=tk.W)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.tab_list, orient=tk.VERTICAL, command=self.tree_dict.yview)
        self.tree_dict.configure(yscroll=scrollbar.set)
        
        self.tree_dict.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def build_contribute_tab(self):
        ttk.Label(self.tab_contribute, text="Đóng góp từ mới hoặc sửa nghĩa", font=("Arial", 11, "bold")).pack(pady=10)
        
        grid_frame = ttk.Frame(self.tab_contribute)
        grid_frame.pack()
        
        ttk.Label(grid_frame, text="Từ vựng:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.contrib_word = ttk.Entry(grid_frame, width=30)
        self.contrib_word.grid(row=0, column=1, pady=5)
        
        ttk.Label(grid_frame, text="Nghĩa:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.contrib_mean = ttk.Entry(grid_frame, width=30)
        self.contrib_mean.grid(row=1, column=1, pady=5)
        
        btn_frame = ttk.Frame(self.tab_contribute)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Gửi yêu cầu THÊM", command=lambda: self.send_contrib("THEM")).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Gửi yêu cầu SỬA", command=lambda: self.send_contrib("SUA")).pack(side=tk.LEFT, padx=10)

    def build_admin_tab(self):
        ttk.Button(self.tab_admin, text=" Tải danh sách chờ", command=self.load_pending_list).pack(anchor=tk.W, pady=(0, 5))
        
        # Bảng Pending
        columns = ("id", "type", "word", "content", "user", "time")
        self.tree_pending = ttk.Treeview(self.tab_admin, columns=columns, show="headings")
        
        self.tree_pending.heading("id", text="ID")
        self.tree_pending.heading("type", text="Loại")
        self.tree_pending.heading("word", text="Từ")
        self.tree_pending.heading("content", text="Nội dung/Nghĩa mới")
        self.tree_pending.heading("user", text="Người gửi")
        self.tree_pending.heading("time", text="Thời gian")
        
        self.tree_pending.column("id", width=0, stretch=tk.NO) # Ẩn cột ID
        self.tree_pending.column("type", width=80)
        self.tree_pending.column("word", width=150)
        self.tree_pending.column("content", width=300)
        self.tree_pending.column("user", width=100)
        self.tree_pending.column("time", width=150)
        
        self.tree_pending.pack(fill=tk.BOTH, expand=True)
        
        # Nút duyệt
        btn_frame = ttk.Frame(self.tab_admin)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text=" DUYỆT (Approve)", command=lambda: self.process_pending("APPROVE")).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text=" TỪ CHỐI (Reject)", command=lambda: self.process_pending("REJECT")).pack(side=tk.LEFT, padx=10)

    # --- LOGIC GIAO TIẾP SERVER ---

    def connect_and_login(self):
        host = self.host_entry.get()
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, DEFAULT_PORT))
            
            # Nhận Welcome
            self.socket.recv(1024)
            
            # Gửi Login
            self.socket.send(f"LOGIN|{user}|{pwd}".encode('utf-8'))
            resp = self.socket.recv(1024).decode('utf-8')
            
            if resp.startswith("SUCCESS"):
                parts = resp.split('|')
                self.user_role = parts[1]
                self.username = user
                self.connected = True
                self.setup_dashboard_ui() # Chuyển sang màn hình chính
                
                # Tự động tải danh sách từ
                self.root.after(100, self.load_dictionary_list)
            else:
                messagebox.showerror("Lỗi", resp)
                self.socket.close()
                
        except Exception as e:
            messagebox.showerror("Kết nối thất bại", str(e))

    def send_request(self, data):
        if not self.socket: return None
        try:
            self.socket.send(data.encode('utf-8'))
            # Tăng buffer size để nhận JSON dài
            response = self.socket.recv(65536).decode('utf-8') 
            return response
        except Exception as e:
            messagebox.showerror("Lỗi mạng", str(e))
            self.logout()
            return None

    def do_lookup(self):
        word = self.search_entry.get()
        if not word: return
        resp = self.send_request(f"TRA|{word}")
        
        self.result_area.delete(1.0, tk.END)
        if resp.startswith("SUCCESS"):
            content = resp.split('|', 1)[1]
            self.result_area.insert(tk.END, content, 'success')
        else:
            self.result_area.insert(tk.END, resp, 'error')

    def load_dictionary_list(self):
        resp = self.send_request("LIST")
        if resp and resp.startswith("LIST_DATA"):
            try:
                json_str = resp.split('|', 1)[1]
                data = json.loads(json_str)
                
                # Xóa dữ liệu cũ trong bảng
                for item in self.tree_dict.get_children():
                    self.tree_dict.delete(item)
                
                # Thêm dữ liệu mới
                for item in data:
                    self.tree_dict.insert("", tk.END, values=(item['word'], item['meaning']))
            except Exception as e:
                print(f"Lỗi parse JSON: {e}")

    def send_contrib(self, action):
        w = self.contrib_word.get()
        m = self.contrib_mean.get()
        if not w or not m:
            messagebox.showwarning("Thiếu tin", "Vui lòng nhập đủ từ và nghĩa")
            return
        
        resp = self.send_request(f"{action}|{w}:{m}")
        if resp.startswith("SUCCESS"):
            messagebox.showinfo("Thành công", resp.split('|', 1)[1])
            self.contrib_word.delete(0, tk.END)
            self.contrib_mean.delete(0, tk.END)
        else:
            messagebox.showerror("Lỗi", resp)

    def load_pending_list(self):
        resp = self.send_request("PENDING")
        if resp and resp.startswith("PENDING_DATA"):
            try:
                json_str = resp.split('|', 1)[1]
                data = json.loads(json_str)
                
                for item in self.tree_pending.get_children():
                    self.tree_pending.delete(item)
                    
                for req in data:
                    # Logic hiển thị nội dung tùy loại
                    content = req.get('meaning', '')
                    if req['type'] == 'update':
                        content = f"{req['old_meaning']} -> {req['new_meaning']}"
                        
                    self.tree_pending.insert("", tk.END, values=(
                        req.get('id', ''), # ID thực (bị ẩn)
                        req['type'],
                        req['word'],
                        content,
                        req['username'],
                        req['timestamp']
                    ))
            except Exception as e:
                print(f"Lỗi parse JSON Pending: {e}")
        elif resp and "Access denied" in resp:
             messagebox.showerror("Quyền hạn", "Bạn không phải Admin")

    def process_pending(self, action):
        # Lấy dòng đang chọn
        selected = self.tree_pending.selection()
        if not selected:
            messagebox.showwarning("Chọn dòng", "Vui lòng chọn một yêu cầu để xử lý")
            return
        
        # Lấy ID từ cột ẩn (cột đầu tiên)
        item_values = self.tree_pending.item(selected[0])['values']
        req_id = item_values[0] # ID nằm ở index 0
        
        resp = self.send_request(f"{action}|{req_id}")
        if resp.startswith("SUCCESS"):
            messagebox.showinfo("Thành công", resp.split('|', 1)[1])
            self.load_pending_list() # Tải lại danh sách sau khi duyệt
            self.load_dictionary_list() # Tải lại danh sách từ (để cập nhật tab 2)
        else:
            messagebox.showerror("Lỗi", resp)

    def logout(self):
        # Gửi lệnh QUIT về server
        try:
            if self.socket and self.connected:
                self.socket.send("QUIT".encode('utf-8'))
        except:
            pass
        
        # Đóng kết nối
        if self.socket: 
            self.socket.close()
            self.socket = None
        
        # Reset trạng thái
        self.connected = False
        self.user_role = None
        self.username = None
        
        # Xóa toàn bộ widget trong main_frame (bao gồm cả notebook)
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # Xóa reference của notebook nếu có
        if hasattr(self, 'notebook'):
            self.notebook = None
        
        # Tạo lại giao diện login (giữ nguyên main_frame)
        # Tiêu đề
        ttk.Label(self.main_frame, text="ĐĂNG NHẬP HỆ THỐNG", font=("Arial", 16, "bold")).pack(pady=20)
        
        # Form nhập liệu
        form_frame = ttk.Frame(self.main_frame)
        form_frame.pack()
        
        ttk.Label(form_frame, text="Server IP:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.host_entry = ttk.Entry(form_frame, width=25)
        self.host_entry.insert(0, DEFAULT_HOST)
        self.host_entry.grid(row=0, column=1, pady=5)
        
        ttk.Label(form_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.user_entry = ttk.Entry(form_frame, width=25)
        self.user_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(form_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.pass_entry = ttk.Entry(form_frame, show="*", width=25)
        self.pass_entry.grid(row=2, column=1, pady=5)
        
        ttk.Button(form_frame, text="Kết nối & Đăng nhập", command=self.connect_and_login).grid(row=3, column=0, columnspan=2, pady=20)
        
        self.status_lbl = ttk.Label(self.main_frame, text="Chưa kết nối", foreground="gray")
        self.status_lbl.pack(side=tk.BOTTOM, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = DictionaryClientGUI(root)
    root.mainloop()