/*
 * 文件名: main.rs
 * 描述: Tauri 桌面应用入口，负责启动本地 Flask 服务并加载 Web 界面。
 * 作用: 让 BackIt 在桌面上像独立 App 一样运行，无需打开 IDE。
 */

use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::{Manager, RunEvent};

struct BackendProcess(Mutex<Option<Child>>);

// 查找可用的 Python 可执行文件，优先使用系统常见路径
fn resolve_python_binary() -> Result<String, String> {
    // 环境变量允许手动指定 Python 路径，便于兼容不同环境
    if let Ok(custom_python) = std::env::var("PYTHON_BIN") {
        if std::path::Path::new(&custom_python).exists() {
            return Ok(custom_python);
        }
    }

    // 依次检查常见 Python 路径，确保在桌面应用环境下仍可定位
    let candidates = vec![
        "/usr/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/local/bin/python3",
        "python3",
    ];

    for candidate in candidates {
        if candidate == "python3" {
            return Ok(candidate.to_string());
        }
        if std::path::Path::new(candidate).exists() {
            return Ok(candidate.to_string());
        }
    }

    Err("未找到可用的 python3，可设置 PYTHON_BIN 指定路径".to_string())
}

// 解析 Python 应用所在目录，优先使用资源目录，其次回退到开发目录
fn resolve_app_dir(app_handle: &tauri::AppHandle) -> Result<std::path::PathBuf, String> {
    // 优先使用打包资源目录，确保发布版本从资源中读取代码
    if let Ok(resource_dir) = app_handle.path().resource_dir() {
        if resource_dir.join("app.py").exists() {
            return Ok(resource_dir);
        }
    }

    // 开发环境下根据当前目录推断项目根目录
    let current_dir = std::env::current_dir().map_err(|err| err.to_string())?;
    let parent_dir = current_dir.join("..");
    if parent_dir.join("app.py").exists() {
        return parent_dir
            .canonicalize()
            .map_err(|err| err.to_string());
    }

    if current_dir.join("app.py").exists() {
        return Ok(current_dir);
    }

    Err("无法找到 app.py，请确认桌面工程与服务代码在同一仓库中".to_string())
}

// 准备可写的数据目录与密钥文件路径，避免写入应用资源目录
fn resolve_data_paths(app_handle: &tauri::AppHandle) -> Result<(std::path::PathBuf, std::path::PathBuf), String> {
    let base_dir = app_handle
        .path()
        .app_data_dir()
        .map_err(|err| err.to_string())?;
    let data_dir = base_dir.join("data");
    let env_path = base_dir.join("ARK_API_KEY.env");
    std::fs::create_dir_all(&data_dir).map_err(|err| err.to_string())?;
    Ok((data_dir, env_path))
}

// 启动 Python 本地服务，并在桌面窗口生命周期内保持运行
fn spawn_backend(app_handle: &tauri::AppHandle) -> Result<Child, String> {
    let app_dir = resolve_app_dir(app_handle)?;
    let (data_dir, env_path) = resolve_data_paths(app_handle)?;
    let cookies_path = data_dir.join("cookies.txt");
    let python_bin = resolve_python_binary()?;

    Command::new(python_bin)
        .current_dir(app_dir)
        .arg("app.py")
        .env("APP_DATA_DIR", data_dir)
        .env("APP_ENV_PATH", env_path)
        .env("APP_COOKIES_PATH", cookies_path)
        .env("PYTHONUNBUFFERED", "1")
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|err| format!("启动后端失败: {}", err))
}

fn main() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            // 在应用启动时拉起后端服务，确保窗口加载即有可用接口
            let backend = match spawn_backend(app.handle()) {
                Ok(child) => Some(child),
                Err(err) => {
                    eprintln!("后端启动失败：{}", err);
                    None
                }
            };

            let state = app.state::<BackendProcess>();
            *state.0.lock().expect("state lock") = backend;
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app_handle, event| {
            // 监听退出事件，确保子进程被干净关闭
            if let RunEvent::ExitRequested { .. } = event {
                let state = app_handle.state::<BackendProcess>();

                // 先取出子进程句柄，避免锁的生命周期影响后续释放流程
                let child_handle = {
                    let mut guard = state.0.lock().expect("state lock");
                    guard.take()
                };

                if let Some(mut child) = child_handle {
                    let _ = child.kill();
                }
            }
        });
}
