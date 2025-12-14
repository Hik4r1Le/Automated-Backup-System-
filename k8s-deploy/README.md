# 📚 Automation Backup System on Kubernetes (K3s)

## 📋 I. Tổng quan cấu hình Cluster

Hệ thống được thiết lập trên **3 máy ảo (VM) Ubuntu** sử dụng **K3s**.

| Node Name        | Vai trò chính | 
|------------------|--------------|
| `k8s-master`     | `Master Node` (Quản lý Cluster) - Node chạy các lệnh kubectl để cấu hình toàn bộ cluster K3s |
| `k8s-worker-1`   | `Worker Node` - Giám sát (Watcher Service)  & Web Admin (Dùng làm giao diện web demo các chức năng chính) | 
| `k8s-worker-2`   | `Worker Node` - Minio (Storage Server) lưu trữ dữ liệu backup dưới dạng Object (giúp sao lưu và phục hồi dữ liệu theo từng version)  | 

---

## 🌐 II. Cấu hình Mạng và IP tĩnh vĩnh viễn trên từng Node (nếu chưa có)

> ⚠️ **Bắt buộc thiết lập IP tĩnh trước khi cài K3s**

> **Áp dụng trên cả 3 NODE**

> **Cả 3 NODE đều cùng 1 mạng NAT trước khi cấu hình IP tĩnh (hỏi ChatGPT nhé)**

### Bước 1: Mở file cấu hình Netplan
```shell
sudo nano /etc/netplan/50-cloud-init.yaml
```

### Bước 2: Thiết lập IP tĩnh cho interface (thường là ens33 nếu dùng Ubuntu)

**Thay đổi IP Address tùy thuộc**

```yaml
network:
  version: 2
  ethernets:
    ens33:
      dhcp4: no
      addresses:
        - 10.0.3.10/24
```

### Bước 3: Áp dụng cấu hình
```shell
sudo netplan apply
```

### Bước 4: Kiểm tra IP của máy Ubuntu
```shell
ip -c a
# hoặc
hostname -I
```

---
## 🚀 III. Cài đặt K3s và Tạo Cluster

### 1. Cài Docker trên cả 3 Node (lần lướt dán từng lệnh trong mỗi khung sau vào termial)

```shell
sudo apt remove $(dpkg --get-selections docker.io docker-compose docker-compose-v2 docker-doc podman-docker containerd runc | cut -f1)
```

```shell
sudo apt update
```
```shell
sudo apt install ca-certificates curl
```
```shell
sudo install -m 0755 -d /etc/apt/keyrings
```
```shell
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
```
```shell
sudo chmod a+r /etc/apt/keyrings/docker.asc
```
```shell
sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF
```
```shell
sudo apt update
```
```shell
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
```shell
sudo usermod -aG docker $USER
```

**Kiểm tra xem Docker tải thành công chưa**

```shell
sudo systemctl status docker
```

### 2. Cài kubectl (chỉ cài trên Node Master)

> **Lần lượt dán từng lệnh trong mỗi khung sau vào terminal của Node Master**

```shell
sudo apt-get update
```

```shell
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
```

```shell
sudo mkdir -p -m 755 /etc/apt/keyrings
```

```shell
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
```

```shell
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

```shell
sudo apt-get update
```

```shell
sudo apt-get install -y kubectl
```

**Kiểm tra đã cài kubectl thành công chưa**

```shell
kubectl version --client
```

### 3. Cài k3sup (chỉ trên Node Master)

```shell
curl -sLS https://get.k3sup.dev | sh
```

```shell
sudo install k3sup /usr/local/bin/
```

**Kiểm tra:**

```shell
k3sup --help
```

### 4. Cài OpenSSH Server (chỉ trên 2 máy Worker Node)

```shell
sudo apt install -y openssh-server
```

### 5. Thiết lập kết nối SSH từ Master Node → Worker Node

**Tạo SSH key trên Master Node**

```shell
ssh-keygen
```

**Trên Master Node copy SSH key sang Worker Nodes**

```shell
ssh-copy-id <username worker node 1>@<ip worker node 1>
ssh-copy-id <username worker node 2>@<ip worker node 2>
```

- Nó sẽ yêu cầu đăng nhập bằng mật khẩu của username.
- Ví dụ nếu username là "nqvuong23" và IP máy Worker Node là "192.168.1.10"

```shell
ssh-copy-id nqvuong23@192.168.1.10
```

**Kiểm tra kết nối SSH từ Master Node tới các Worker Node có thành công không**

- Thực hiên trên Master Node

```shell
ssh <username worker node 1>@<ip worker node 1>
ssh <username worker node 1>@<ip worker node 1>
```

### 6. Dùng k3sup tạo K3s Cluster

**Trên Master Node**

```shell
k3sup install --ip 192.168.125.100 --user nqvuong23
```

- "192.168.125.100": IP của Master Node (ví dụ)
- "nqvuong23": username của Master Node (ví dụ)

### 7. Join các Worker Node vào K3s Cluster

**Thực hiện các lệnh sau đều trên Master Node:**

```shell
k3sup join \
  --ip 192.168.125.101 \
  --server-ip 192.168.125.100 \
  --user nqvuong23
```

- "192.168.125.101": IP của Worker Node 1 (ví dụ)
- "nqvuong23": username của Worker Node 1 (ví dụ)

```shell
k3sup join \
  --ip 192.168.125.102 \
  --server-ip 192.168.125.100 \
  --user nqvuong23
```

- "192.168.125.102": IP của Worker Node 2 (ví dụ)
- "nqvuong23": username của Worker Node 2 (ví dụ)

### 8. Kiểm tra Cluster sau khi tạo 
**Trên Master Node**
```shell
kubectl get nodes -o wide
```

### 9. Đổi Hostname và gán nhãn cho 2 Node Worker
**Thực hiện lệnh sau trên Master Node**
```shell
sudo hostnamectl set-hostname k3s-master
```
```shell
kubectl label node k3s-worker-1 storage-role=source
kubectl label node k3s-worker-2 storage-role=target
```
**Thực hiện lệnh sau trên Worker Node 1**
```shell
sudo hostnamectl set-hostname k3s-worker-1
```
**Thực hiện lệnh sau trên Worker Node 2**
```shell
sudo hostnamectl set-hostname k3s-worker-2
```

**Quan trong: reboote lại toàn bộ cả 3 Node**
```shell
sudo reboot
```

---
## 💾 IV. Chuẩn bị Thư mục HostPath

**Trên Worker Node 1**
```shell
# Thư mục nguồn (Watcher và Web Admin sử dụng)
sudo mkdir -p /mnt/source
sudo chmod 777 /mnt/source

# Thư mục logs
sudo mkdir -p /mnt/logs
sudo chmod 777 /mnt/logs
```

**Trên Worker Node 2**

```shell
# Thư mục lưu trữ vật lý cho MinIO
sudo mkdir -p /mnt/minio-storage-data
sudo chmod 777 /mnt/minio-storage-data
```

---
## ⚙️ V. Các Bước Deploy (Triển khai Tài nguyên K8s)
**Chỉ áp dụng trên MASTER NODE cho toàn bộ các lệnh sau**
```shell
# Sau khi pull github repo về máy thì dùng lệnh
cd Automated-Backup-System-/k8s-deploy/

# Tạo Secret 
kubectl create secret generic minio-secret --from-literal=MINIO_ACCESS_KEY='minioadmin' --from-literal=MINIO_SECRET_KEY='minioadmin'

# Deploy MinIO (Storage Server)
kubectl apply -f minio-deployment.yaml
kubectl apply -f minio-service.yaml

# Deploy Watcher Service
kubectl apply -f watcher-configmap.yaml
kubectl apply -f watcher-deployment.yaml

# Deploy Web Admin UI
kubectl apply -f web-admin-deployment.yaml
kubectl apply -f web-admin-service.yaml
```

---
## ✅ VI. Kiểm tra Resource và Truy cập
**Chỉ áp dụng trên MASTER NODE**

### 1. Kiểm tra Trạng thái Pods và Services
```shell
kubectl get pods 
kubectl get svc 
```

### 2. Kiểm tra Kết quả trên Trình duyệt

**Giả sử kết quả trả về của lệnh `kubectl get svc` như sau:**

```shell
NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
kubernetes               ClusterIP   10.96.0.1       <none>        443/TCP          2d6h
minio-console-nodeport   NodePort    10.106.145.24   <none>        9001:30967/TCP   11h
storage-service          ClusterIP   10.110.1.164    <none>        9000/TCP         11h
web-admin-nodeport       NodePort    10.102.99.100   <none>        8080:32437/TCP   6h35m
```

- Bạn có thể thấy có 2 service kiểu `NodePort`, ta sẽ dùng 2 `PORT` của 2 service này để truy cập vào trình duyệt xem giao diện web Minio và giao diện web Demo

**Sử dụng "IP Address" của 1 trong 3 Node đều được**

```shell
# Service của Minio có PORT là "9001:30967/TCP", vậy ta sẽ dùng URL sau:
http://<IP Address>:30967

# Service của Web Admin có PORT là "8080:32437/TCP", vậy ta sẽ dùng URL sau:
http://<IP Address>:32437
```

> **Lưu ý: khi vào trang web của Minio nó sẽ yêu cầu login, username và password đều là `minioadmin`**
