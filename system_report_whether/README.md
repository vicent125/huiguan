# 智能水肥一体化系统

项目由 Flask 后端和 Vue 3 前端组成。本地开发默认使用
`backend/instance/smart_agriculture.db`，不要求额外安装 MySQL。

## VS Code 一键联调

1. 在 VS Code 中打开本项目根目录，不要只打开 `frontend` 文件夹。
2. 打开“运行和调试”，选择“前后端联调”。
3. 按 `F5`。后端运行在 `http://127.0.0.1:5000`，前端运行在
   `http://127.0.0.1:5173`。

项目配置使用 `npm.cmd`，可避开 Windows PowerShell 禁止执行 `npm.ps1`
时产生的启动错误。

## 手动启动

后端：

```powershell
cd backend
.\venv\Scripts\python.exe app.py
```

前端（另开一个终端）：

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

如需连接 MySQL，在启动后端前设置 `DATABASE_URL`，例如：

```powershell
$env:DATABASE_URL='mysql+pymysql://用户名:密码@localhost:3306/smart_agriculture'
```
