# 班主任兼语文教师工作台

这是一个单人、本地存储的 Streamlit 工作台。数据写入 `data/`，上传文件写入 `uploads/`，不需要数据库和登录。

## 运行

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

浏览器打开 `http://localhost:8501`。程序运行期间保持窗口开启即可使用页面。
