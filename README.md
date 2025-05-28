# 桃奈酱 Telegram Bot

本项目一键部署至 Render，无需 .env 文件。

## 快速开始

1. **克隆仓库：**
   ```bash
   git clone https://github.com/<你的用户名>/<你的仓库名>.git
   cd <你的仓库名>
   ```

2. **配置 Render：**
   - 在 Render 控制台新建 Web Service，连接本仓库
   - Render 会读取 `render.yaml` 自动安装依赖并启动

3. **部署完成后：**
   - 在 Telegram 中发送 `/start`，即可查看主菜单

## 环境变量

- **BOT_TOKEN**：7544494246:AAFa5XauMronkG5xSpIXBHpLk7mmQzDZS-A  
- **OWNER_USERNAME**：baby_520（不带 `@`）  
- **WEBHOOK_DOMAIN**：https://taonaijiang.onrender.com  

## 功能

- `/start` 主菜单  
- 📊 今日 USDT C2C 价格查询  
- 🔑 绑定 OpenAI API Key  
- ChatGPT 聊天（优先 GPT-4o，失败自动降级 GPT-3.5）  
- ⚙️ 开发者后台（查看日志、清理缓存）  
