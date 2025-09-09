# GCP防火墙配置指南

## 概述
本指南将帮助您在GCP控制台中配置防火墙规则，使情感分析系统能够通过公网IP访问。

## 配置步骤

### 方法一：通过GCP控制台配置

1. **登录GCP控制台**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 选择您的项目

2. **进入防火墙设置**
   - 在左侧菜单中，点击 **VPC网络** > **防火墙**
   - 点击 **创建防火墙规则**

3. **创建HTTP访问规则**
   - **名称**: `sentiment-analysis-http`
   - **描述**: `Allow HTTP access to sentiment analysis application`
   - **网络**: `default` (或您使用的VPC网络)
   - **优先级**: `1000`
   - **方向**: `入站`
   - **操作**: `允许`
   - **目标**: `网络中的所有实例`
   - **来源IP范围**: `0.0.0.0/0`
   - **协议和端口**: 
     - 选择 **指定的协议和端口**
     - 勾选 **TCP**
     - 端口: `80,8000`

4. **创建SSH访问规则**（如果不存在）
   - **名称**: `allow-ssh`
   - **描述**: `Allow SSH access`
   - **网络**: `default`
   - **优先级**: `1000`
   - **方向**: `入站`
   - **操作**: `允许`
   - **目标**: `网络中的所有实例`
   - **来源IP范围**: `0.0.0.0/0` (建议限制为您的IP)
   - **协议和端口**: 
     - 选择 **指定的协议和端口**
     - 勾选 **TCP**
     - 端口: `22`

5. **保存规则**
   - 点击 **创建** 保存防火墙规则

### 方法二：通过gcloud命令行配置

如果您有gcloud CLI工具，可以使用以下命令：

```bash
# 创建HTTP访问规则
gcloud compute firewall-rules create sentiment-analysis-http \
    --allow tcp:80,tcp:8000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP access to sentiment analysis application"

# 创建SSH访问规则
gcloud compute firewall-rules create allow-ssh \
    --allow tcp:22 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow SSH access"
```

### 方法三：通过Terraform配置

如果您使用Terraform管理基础设施：

```hcl
resource "google_compute_firewall" "sentiment_analysis_http" {
  name    = "sentiment-analysis-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["sentiment-analysis"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["sentiment-analysis"]
}
```

## 验证配置

### 1. 检查防火墙规则
```bash
# 列出所有防火墙规则
gcloud compute firewall-rules list

# 查看特定规则详情
gcloud compute firewall-rules describe sentiment-analysis-http
```

### 2. 测试网络连接
```bash
# 测试HTTP端口
curl -I http://35.209.254.98

# 测试应用端口
curl -I http://35.209.254.98:8000

# 测试健康检查接口
curl http://35.209.254.98/api/health
```

### 3. 检查虚拟机网络标签
确保您的虚拟机实例有正确的网络标签：

```bash
# 查看实例详情
gcloud compute instances describe your-instance-name --zone=your-zone

# 添加网络标签（如果需要）
gcloud compute instances add-tags your-instance-name \
    --tags sentiment-analysis \
    --zone your-zone
```

## 安全建议

### 1. 限制SSH访问
为了安全起见，建议将SSH访问限制为您的IP地址：

```bash
# 获取您的公网IP
curl ifconfig.me

# 更新SSH规则，限制来源IP
gcloud compute firewall-rules update allow-ssh \
    --source-ranges YOUR_IP_ADDRESS/32
```

### 2. 使用HTTPS（推荐）
配置SSL证书以使用HTTPS：

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 更新防火墙规则，添加HTTPS端口
gcloud compute firewall-rules create sentiment-analysis-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS access"
```

### 3. 配置负载均衡器
对于生产环境，建议使用GCP负载均衡器：

```bash
# 创建健康检查
gcloud compute health-checks create http sentiment-health-check \
    --port 8000 \
    --request-path /api/health

# 创建后端服务
gcloud compute backend-services create sentiment-backend \
    --protocol HTTP \
    --health-checks sentiment-health-check \
    --global

# 创建URL映射
gcloud compute url-maps create sentiment-url-map \
    --default-service sentiment-backend

# 创建目标代理
gcloud compute target-http-proxies create sentiment-proxy \
    --url-map sentiment-url-map

# 创建全局转发规则
gcloud compute forwarding-rules create sentiment-forwarding-rule \
    --global \
    --target-http-proxy sentiment-proxy \
    --ports 80
```

## 故障排除

### 1. 无法访问应用
检查以下项目：
- 防火墙规则是否正确创建
- 虚拟机实例是否有正确的网络标签
- 应用服务是否正在运行
- 端口是否正确监听

### 2. 连接超时
```bash
# 检查虚拟机状态
gcloud compute instances list

# 检查网络连接
ping 35.209.254.98

# 检查端口是否开放
nmap -p 80,8000 35.209.254.98
```

### 3. 权限问题
确保您的GCP账户有足够的权限：
- `compute.firewalls.create`
- `compute.firewalls.update`
- `compute.instances.list`

## 监控和日志

### 1. 启用防火墙日志
```bash
# 启用防火墙日志记录
gcloud compute firewall-rules update sentiment-analysis-http \
    --enable-logging
```

### 2. 查看防火墙日志
在GCP控制台中：
- 进入 **日志记录** > **日志浏览器**
- 选择资源类型：`GCE防火墙规则`
- 查看被阻止或允许的连接

### 3. 设置告警
```bash
# 创建日志指标
gcloud logging metrics create firewall_blocked_connections \
    --description "Blocked firewall connections" \
    --log-filter 'resource.type="gce_firewall_rule" AND jsonPayload.disposition="DENIED"'

# 创建告警策略
gcloud alpha monitoring policies create \
    --policy-from-file=firewall-alert-policy.yaml
```

## 最佳实践

1. **最小权限原则**：只开放必要的端口
2. **定期审查**：定期检查和更新防火墙规则
3. **使用标签**：为虚拟机实例添加适当的网络标签
4. **监控访问**：启用防火墙日志记录
5. **备份配置**：定期备份防火墙配置

## 联系支持

如果遇到防火墙配置问题，请提供：
1. 防火墙规则列表：`gcloud compute firewall-rules list`
2. 虚拟机实例详情：`gcloud compute instances describe your-instance`
3. 网络连接测试结果：`curl -I http://35.209.254.98`
4. 相关错误日志


