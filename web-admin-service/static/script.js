// script.js (Đã cập nhật logic UI)

const API_BASE_URL = '/api'; 
let currentFile = null;

const fileListUl = document.getElementById('file-list');
const filenameSpan = document.getElementById('current-filename');
const editor = document.getElementById('file-content-editor');
const saveBtn = document.getElementById('save-btn');
const deleteBtn = document.getElementById('delete-btn');
const createNewBtn = document.getElementById('create-new-btn');
const statusMessage = document.getElementById('status-message'); // Cho Editor
const backupListContainer = document.getElementById('backup-list-container'); // Mới
const backupStatusMessage = document.getElementById('backup-status-message'); // Mới


// Hàm 1: Reset trạng thái soạn thảo (Yêu cầu 1)
function resetEditorState() {
    currentFile = null;
    filenameSpan.textContent = 'Choose or add new file';
    editor.value = '';
    editor.disabled = true;
    saveBtn.disabled = true;
    deleteBtn.disabled = true;
    
    // Gỡ active khỏi tất cả các mục trong danh sách
    document.querySelectorAll('#file-list li').forEach(li => li.classList.remove('active'));
}

// Hàm hiển thị thông báo
function showStatus(message, type = 'success', target = statusMessage) {
    target.textContent = message;
    target.className = type;
    target.classList.remove('hidden');
    setTimeout(() => {
        target.classList.add('hidden');
    }, 3000);
}

// ----------------------------------------------------
// A. Tải và Hiển thị Danh sách File
// ----------------------------------------------------
async function loadFiles() {
    try {
        const response = await fetch(`${API_BASE_URL}/files`);
        const data = await response.json();
        
        fileListUl.innerHTML = '';
        if (data.files.length === 0) {
            fileListUl.innerHTML = '<li class="empty-message">No files found.</li>';
            return;
        }

        data.files.forEach(filename => {
            const li = document.createElement('li');
            li.textContent = filename;
            li.dataset.filename = filename;
            li.addEventListener('click', () => selectFile(filename));
            fileListUl.appendChild(li);
        });

    } catch (error) {
        showStatus('Error loading files!', 'error');
        console.error('Error loading files:', error);
    }
}

// ----------------------------------------------------
// B. Chọn File để Chỉnh sửa
// ----------------------------------------------------
async function selectFile(filename) {
    // 1. Cập nhật trạng thái UI
    currentFile = filename;
    filenameSpan.textContent = filename;
    editor.disabled = false;
    saveBtn.disabled = false;
    deleteBtn.disabled = false;
    
    // Gỡ active khỏi tất cả và thêm vào file được chọn
    document.querySelectorAll('#file-list li').forEach(li => li.classList.remove('active'));
    document.querySelector(`[data-filename="${filename}"]`).classList.add('active');

    // 2. Tải nội dung
    try {
        const response = await fetch(`${API_BASE_URL}/file/${filename}`);
        if (!response.ok) {
            throw new Error('Unable to read file content.');
        }
        const data = await response.json();
        editor.value = data.content;

    } catch (error) {
        showStatus(error.message || 'Error reading file!', 'error');
        editor.value = '';
    }
}

// ----------------------------------------------------
// C. Tạo File Mới (Logic đã sửa đổi - Yêu cầu 2)
// ----------------------------------------------------
createNewBtn.addEventListener('click', async () => {
    const newFilename = prompt("Enter new file name (Ex: config.txt):");
    
    if (newFilename) {
        // Kiểm tra xem file đã tồn tại trên UI chưa
        if (document.querySelector(`[data-filename="${newFilename}"]`)) {
            alert("File name already exists. Please choose a different name.");
            return;
        }

        // 1. Gọi API POST để tạo file rỗng ngay lập tức
        try {
            const response = await fetch(`${API_BASE_URL}/file/${newFilename}`, {
                method: 'POST', 
                headers: {
                    'Content-Type': 'application/json',
                },
                // Gửi nội dung trống để tạo file rỗng
                body: JSON.stringify({ content: '' }), 
            });

            const data = await response.json();
            if (response.ok) {
                showStatus(`Created empty file "${newFilename}". Start editing.`, 'success');
                
                // 2. Tải lại danh sách file và chọn file vừa tạo
                await loadFiles(); 
                selectFile(newFilename); 

            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            showStatus('Error creating file: ' + error.message, 'error');
            console.error('Error creating file:', error);
        }
    }
});


// ----------------------------------------------------
// D. Lưu File (Cập nhật nội dung)
// ----------------------------------------------------
saveBtn.addEventListener('click', async () => {
    if (!currentFile) return;

    const url = `${API_BASE_URL}/file/${currentFile}`;
    
    // Luôn dùng PUT cho việc cập nhật sau khi file đã tồn tại
    try {
        const response = await fetch(url, {
            method: 'PUT', 
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content: editor.value }),
        });

        const data = await response.json();
        if (response.ok) {
            showStatus('File updated successfully.', 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        showStatus('Save error: ' + error.message, 'error');
        console.error('Save error:', error);
    }
});

// ----------------------------------------------------
// E. Xóa File
// ----------------------------------------------------
deleteBtn.addEventListener('click', async () => {
    if (!currentFile || !confirm(`Are you sure you want to delete the file "${currentFile}"?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/file/${currentFile}`, {
            method: 'DELETE',
        });

        const data = await response.json();
        if (response.ok) {
            showStatus(data.message, 'success');
            
            // 1. Reset UI về trạng thái ban đầu (thay vì chỉ xóa file)
            resetEditorState(); 
            
            // 2. Tải lại danh sách
            await loadFiles(); 
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        showStatus('Delete error: ' + error.message, 'error');
        console.error('Delete error:', error);
    }
});

// ----------------------------------------------------
// F. Tải và Hiển thị Danh sách Backup (MỚI)
// ----------------------------------------------------
async function loadBackupHistory() {
    backupListContainer.innerHTML = '<div class="loading-message">Loading history...</div>';
    try {
        const response = await fetch(`${API_BASE_URL}/backup/versions`);
        const data = await response.json(); // Data là object {filename: [version_list], ...}

        backupListContainer.innerHTML = '';
        if (Object.keys(data).length === 0) {
            backupListContainer.innerHTML = '<div class="loading-message">No backup versions found.</div>';
            return;
        }

        // Duyệt qua từng file gốc (key)
        for (const [baseName, versions] of Object.entries(data)) {
            const groupDiv = document.createElement('div');
            groupDiv.className = 'backup-group';

            // Header (Dropdown Trigger)
            const header = document.createElement('div');
            header.className = 'backup-file-header';
            header.innerHTML = `
                ${baseName} <span>(${versions.length} versions)</span>
            `;
            
            // List Versions (Ẩn ban đầu)
            const ul = document.createElement('ul');
            ul.className = 'version-list';
            
            // Logic cho Dropdown
            header.addEventListener('click', () => {
                ul.classList.toggle('expanded');
            });
            
            // Duyệt qua từng phiên bản (version)
            // Sắp xếp ngược để thấy phiên bản mới nhất trước
            versions.sort((a, b) => new Date(b.last_modified) - new Date(a.last_modified)).forEach(version => {
                const li = document.createElement('li');
                
                // Chuẩn hóa thời gian
                const date = new Date(version.last_modified);
                const timeStr = date.toLocaleTimeString();
                const dateStr = date.toLocaleDateString();
                
                li.innerHTML = `
                    <div class="version-info">
                        <strong>Key: ${version.key}</strong>
                        <span class="version-time">Modified: ${dateStr} ${timeStr}</span>
                        <span class="version-time">Size: ${formatBytes(version.size)}</span>
                    </div>
                    <button class="restore-action-btn" data-key="${version.key}">Restore</button>
                `;
                
                // Gán sự kiện cho nút Restore
                li.querySelector('.restore-action-btn').addEventListener('click', (e) => {
                    e.stopPropagation(); // Ngăn sự kiện click lan ra dropdown
                    handleRestore(version.key, baseName);
                });
                
                ul.appendChild(li);
            });
            
            groupDiv.appendChild(header);
            groupDiv.appendChild(ul);
            backupListContainer.appendChild(groupDiv);
        }

    } catch (error) {
        showStatus('Error loading backup history!', 'error', backupStatusMessage);
        console.error('Error loading backup history:', error);
    }
}

// ----------------------------------------------------
// G. Xử lý Phục hồi (Restore)
// ----------------------------------------------------
async function handleRestore(objectKey, baseName) {
    if (!confirm(`Are you sure you want to RESTORE file "${baseName}" using version key "${objectKey}"? This will overwrite the current source file.`)) {
        return;
    }
    
    showStatus(`Restoring ${baseName}...`, 'info', backupStatusMessage);

    // Encode Key vì nó có thể chứa ký tự đặc biệt (ví dụ: dấu chấm)
    const encodedKey = encodeURIComponent(objectKey);
    const url = `${API_BASE_URL}/backup/restore/${encodedKey}`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        });

        const data = await response.json();

        if (response.ok) {
            showStatus(data.message, 'success', backupStatusMessage);
            // Sau khi restore thành công, tải lại danh sách file nguồn
            await loadFiles(); 
            // Chọn file vừa được restore để người dùng thấy nội dung
            selectFile(baseName); 
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        showStatus('RESTORE FAILED: ' + error.message, 'error', backupStatusMessage);
        console.error('Restore error:', error);
    }
}

// ----------------------------------------------------
// H. Hàm tiện ích (Định dạng Kích thước File)
// ----------------------------------------------------
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

// ----------------------------------------------------
// Khởi động ứng dụng (ĐÃ SỬA ĐỔI)
// ----------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    loadFiles();
    loadBackupHistory(); // Tải lịch sử backup khi khởi tạo
    resetEditorState(); 
});
