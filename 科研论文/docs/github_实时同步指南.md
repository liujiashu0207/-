# GitHub 实时同步指南

## 现状说明
当前环境里 `git` 还不可用（你刚才取消了安装弹窗），所以自动同步脚本已准备好，但还需要先完成 Git 安装并授权。

## 一次性配置（只做一次）

1. 安装 Git（手动确认安装弹窗）  
2. 在项目根目录运行：

```powershell
cd "c:\Users\33839\Desktop\科研论文"
.\scripts\setup_git_sync.ps1 -RemoteUrl "https://github.com/你的用户名/你的仓库.git"
```

> 如果你使用 SSH：
>
> `.\scripts\setup_git_sync.ps1 -RemoteUrl "git@github.com:你的用户名/你的仓库.git"`

## 手动一键同步（推荐）

```powershell
.\scripts\sync_to_github.ps1 -Message "本次改动说明"
```

## 自动循环同步（近实时）

```powershell
.\scripts\auto_sync_watch.ps1 -IntervalSeconds 60
```

- 每 60 秒检查一次变更
- 有变更就自动 add/commit/push
- 用 `Ctrl + C` 停止

## 给 Manus 的固定审查入口
建议每次同步后让 Manus 优先审：

1. `docs/结论-证据对照表_v1.md`
2. `results/exp_multiseed_significance.csv`
3. `docs/对标评审_科学严谨性_v1.md`

这样 Manus 会按科研严谨性审查，不会只给泛化建议。

