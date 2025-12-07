import socket
import threading
import json
import os
from datetime import datetime

class DictionaryServer:
    def __init__(self, host='localhost', port=5555, dict_file='dictionary.json', pending_file='pending.json'):
        self.host = host
        self.port = port
        self.dict_file = dict_file
        self.pending_file = pending_file
        self.dictionary = {}
        self.pending = {}
        self.lock = threading.Lock()
        self.pending_lock = threading.Lock()
        self.client_count = 0
        
        # User credentials (in production, use hashed passwords and database)
        self.users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'user1': {'password': 'user123', 'role': 'user'},
            'user2': {'password': 'user123', 'role': 'user'}
        }
        
        self.load_data()
        
    def load_data(self):
        """Load dictionary and pending requests from files"""
        # Load dictionary
        if os.path.exists(self.dict_file):
            try:
                with open(self.dict_file, 'r', encoding='utf-8') as f:
                    self.dictionary = json.load(f)
                print(f"✓ Loaded {len(self.dictionary)} words from {self.dict_file}")
            except Exception as e:
                print(f"✗ Error loading dictionary: {e}")
                self.dictionary = {}
        else:
            self.dictionary = {
                'hello': 'xin chào',
                'world': 'thế giới',
                'python': 'ngôn ngữ lập trình Python',
                'computer': 'máy tính',
                'network': 'mạng máy tính'
            }
            self.save_dictionary()
            print(f"✓ Created new dictionary with {len(self.dictionary)} default words")
        
        # Load pending requests
        if os.path.exists(self.pending_file):
            try:
                with open(self.pending_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Ensure it's a dictionary
                    if isinstance(data, dict):
                        self.pending = data
                    else:
                        self.pending = {}
                print(f"✓ Loaded {len(self.pending)} pending requests from {self.pending_file}")
            except Exception as e:
                print(f"✗ Error loading pending: {e}")
                self.pending = {}
        else:
            self.pending = {}
            self.save_pending()
            print(f"✓ Created new pending file")
    
    def save_dictionary(self):
        """Save dictionary data to file"""
        try:
            with open(self.dict_file, 'w', encoding='utf-8') as f:
                json.dump(self.dictionary, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"✗ Error saving dictionary: {e}")
            return False
    
    def save_pending(self):
        """Save pending requests to file"""
        try:
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(self.pending, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"✗ Error saving pending: {e}")
            return False
    
    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        client_id = self.client_count
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} connected from {address}")
        
        user_role = None
        username = None
        
        try:
            # Authentication
            welcome = "WELCOME|Dictionary Server v2.0 - Please Login"
            client_socket.send(welcome.encode('utf-8'))
            
            # Wait for login
            auth_data = client_socket.recv(1024).decode('utf-8').strip()
            auth_response = self.authenticate(auth_data)
            
            if auth_response.startswith("SUCCESS"):
                username = auth_data.split('|')[1]
                user_role = self.users[username]['role']
                print(f"[Client #{client_id}] User '{username}' logged in as {user_role}")
            
            client_socket.send(auth_response.encode('utf-8'))
            
            if not auth_response.startswith("SUCCESS"):
                return
            
            while True:
                data = client_socket.recv(4096).decode('utf-8').strip()
                
                if not data:
                    break
                
                print(f"[Client #{client_id}] {username} ({user_role}): {data}")
                
                # Process request with role
                response = self.process_request(data, user_role, username)
                
                client_socket.send(response.encode('utf-8'))
                
                if data.upper() == 'QUIT':
                    break
                    
        except Exception as e:
            print(f"[Client #{client_id}] Error: {e}")
        finally:
            client_socket.close()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Client #{client_id} disconnected")
    
    def authenticate(self, auth_data):
        """Authenticate user"""
        try:
            parts = auth_data.split('|')
            if len(parts) != 3 or parts[0].upper() != 'LOGIN':
                return "ERROR|Invalid login format. Use: LOGIN|username|password"
            
            username = parts[1]
            password = parts[2]
            
            if username in self.users and self.users[username]['password'] == password:
                role = self.users[username]['role']
                return f"SUCCESS|{role}|Login successful as {role}"
            else:
                return "ERROR|Invalid username or password"
                
        except Exception as e:
            return f"ERROR|Authentication error: {e}"
    
    def process_request(self, request, role, username):
        parts = request.split('|', 1)
        if len(parts) < 1: return "ERROR|Invalid request format"
        command = parts[0].upper()
        
        # LOOKUP word (both roles)
        

        if command == 'TRA':
            if len(parts) < 2:
                return "ERROR|Usage: TRA|word"
            word = parts[1].lower().strip()
            
            with self.lock:
                if word in self.dictionary:
                    return f"SUCCESS|{word}: {self.dictionary[word]}"
                else:
                    return f"NOTFOUND|Word '{word}' not found in dictionary"
                
                
        elif command == 'LIST':
            with self.lock:
                # Chuyển đổi dictionary thành danh sách các object để Client dễ xử lý
                # Sắp xếp luôn theo key (word)
                data = [{"word": w, "meaning": m} for w, m in sorted(self.dictionary.items())]
                # Trả về với header riêng là LIST_DATA
                return f"LIST_DATA|{json.dumps(data, ensure_ascii=False)}"

        elif command == 'PENDING':
            if role != 'admin': return "ERROR|Access denied"
            
            with self.pending_lock:
                # Chuyển pending dict thành list có kèm ID để Client hiển thị
                pending_list = []
                for req_id, req in self.pending.items():
                    item = req.copy()
                    item['id'] = req_id # Đính kèm ID vào để client biết user chọn dòng nào
                    pending_list.append(item)
                
                return f"PENDING_DATA|{json.dumps(pending_list, ensure_ascii=False)}"

        # ADD new word (user role - goes to pending)
        elif command == 'THEM':
            if len(parts) < 2 or ':' not in parts[1]:
                return "ERROR|Usage: THEM|word:meaning"
            
            try:
                word, meaning = parts[1].split(':', 1)
                word = word.lower().strip()
                meaning = meaning.strip()
                
                if not word or not meaning:
                    return "ERROR|Word and meaning cannot be empty"
                
                with self.lock:
                    if word in self.dictionary:
                        return f"ERROR|Word '{word}' already exists"
                
                # Add to pending
                with self.pending_lock:
                    request_id = f"{word}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.pending[request_id] = {
                        'type': 'add',
                        'word': word,
                        'meaning': meaning,
                        'username': username,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.save_pending()
                    
                return f"SUCCESS|Request submitted for approval\nWord: {word}\nMeaning: {meaning}"
                        
            except ValueError:
                return "ERROR|Invalid format. Use: THEM|word:meaning"
        
        # UPDATE existing word (user role - goes to pending)
        elif command == 'SUA':
            if len(parts) < 2 or ':' not in parts[1]:
                return "ERROR|Usage: SUA|word:meaning"
            
            try:
                word, meaning = parts[1].split(':', 1)
                word = word.lower().strip()
                meaning = meaning.strip()
                
                if not word or not meaning:
                    return "ERROR|Word and meaning cannot be empty"
                
                with self.lock:
                    if word not in self.dictionary:
                        return f"ERROR|Word '{word}' not found"
                    old_meaning = self.dictionary[word]
                
                # Add to pending
                with self.pending_lock:
                    request_id = f"{word}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    self.pending[request_id] = {
                        'type': 'update',
                        'word': word,
                        'old_meaning': old_meaning,
                        'new_meaning': meaning,
                        'username': username,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    self.save_pending()
                    
                return f"SUCCESS|Update request submitted for approval\nWord: {word}\nOld: {old_meaning}\nNew: {meaning}"
                        
            except ValueError:
                return "ERROR|Invalid format. Use: SUA|word:meaning"
        
        # LIST all words (both roles)
        elif command == 'LIST':
            with self.lock:
                if not self.dictionary:
                    return "SUCCESS|Dictionary is empty"
                
                word_list = '\n'.join([f"  • {word}: {meaning}" 
                                      for word, meaning in sorted(self.dictionary.items())])
                return f"SUCCESS|Dictionary ({len(self.dictionary)} words):\n{word_list}"
        
        # LIST pending requests (admin only)
        elif command == 'PENDING':
            if role != 'admin':
                return "ERROR|Access denied. Admin only"
            
            with self.pending_lock:
                # Ensure pending is a dictionary
                if not isinstance(self.pending, dict):
                    self.pending = {}
                    self.save_pending()
                
                if not self.pending:
                    return "SUCCESS|No pending requests"
                
                pending_list = []
                try:
                    for req_id, req in self.pending.items():
                        if req['type'] == 'add':
                            pending_list.append(
                                f"  [{req_id}]\n"
                                f"    Type: ADD\n"
                                f"    Word: {req['word']}\n"
                                f"    Meaning: {req['meaning']}\n"
                                f"    By: {req['username']} at {req['timestamp']}"
                            )
                        else:
                            pending_list.append(
                                f"  [{req_id}]\n"
                                f"    Type: UPDATE\n"
                                f"    Word: {req['word']}\n"
                                f"    Old: {req['old_meaning']}\n"
                                f"    New: {req['new_meaning']}\n"
                                f"    By: {req['username']} at {req['timestamp']}"
                            )
                    
                    return f"SUCCESS|Pending Requests ({len(self.pending)}):\n" + '\n\n'.join(pending_list)
                except Exception as e:
                    return f"ERROR|Failed to process pending requests: {str(e)}"
        
        # APPROVE request (admin only)
        elif command == 'APPROVE':
            if role != 'admin':
                return "ERROR|Access denied. Admin only"
            
            if len(parts) < 2:
                return "ERROR|Usage: APPROVE|request_id"
            
            request_id = parts[1].strip()
            
            with self.pending_lock:
                if request_id not in self.pending:
                    return f"ERROR|Request '{request_id}' not found"
                
                req = self.pending[request_id]
                
                with self.lock:
                    if req['type'] == 'add':
                        self.dictionary[req['word']] = req['meaning']
                        result = f"Added '{req['word']}': {req['meaning']}"
                    else:
                        self.dictionary[req['word']] = req['new_meaning']
                        result = f"Updated '{req['word']}' to: {req['new_meaning']}"
                    
                    self.save_dictionary()
                
                del self.pending[request_id]
                self.save_pending()
                
                return f"SUCCESS|Request approved!\n{result}"
        
        # REJECT request (admin only)
        elif command == 'REJECT':
            if role != 'admin':
                return "ERROR|Access denied. Admin only"
            
            if len(parts) < 2:
                return "ERROR|Usage: REJECT|request_id"
            
            request_id = parts[1].strip()
            
            with self.pending_lock:
                if request_id not in self.pending:
                    return f"ERROR|Request '{request_id}' not found"
                
                req = self.pending[request_id]
                del self.pending[request_id]
                self.save_pending()
                
                return f"SUCCESS|Request rejected\nWord: {req['word']}"
        
        # QUIT
        elif command == 'QUIT':
            return "SUCCESS|Goodbye!"
        
        else:
            return f"ERROR|Unknown command: {command}"
    
    def start(self):
        """Start the server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"\n{'='*60}")
            print(f"📖 Dictionary Server Started (v2.0)")
            print(f"{'='*60}")
            print(f"Host: {self.host}")
            print(f"Port: {self.port}")
            print(f"Dictionary file: {self.dict_file}")
            print(f"Pending file: {self.pending_file}")
            print(f"Words in dictionary: {len(self.dictionary)}")
            print(f"Pending requests: {len(self.pending)}")
            print(f"\nAccounts:")
            for user, info in self.users.items():
                print(f"  {user} ({info['role']}) - password: {info['password']}")
            print(f"\nWaiting for connections...\n")
            
            while True:
                client_socket, address = server_socket.accept()
                self.client_count += 1
                
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                
        except KeyboardInterrupt:
            print("\n\nServer shutting down...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()
            print("Server closed")

if __name__ == "__main__":
    server = DictionaryServer(host='localhost', port=5555)
    server.start()