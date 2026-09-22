# 安全策略

## 报告漏洞

请使用 GitHub 的 **Private vulnerability reporting**（本仓 Security 标签页 → Report a vulnerability），
**不要**在公开 issue 中描述可利用细节。

## 范围

- `assets/*/addon.py`、`brickfly_mcp.py`（Blender 内 socket 服务，9876 端口，接受 bpy 代码执行）
- `assets/*/` 内的服务端 wheel（stdio MCP 服务端）
- 发行签名与校验链（`assets/release-signing/`）

## 非范围

- Blender 本体漏洞（报 blender.org）
- 用户自有场景文件损坏（本包默认不触碰用户资产，见 SKILL.md 七条铁律）

## 已知安全设计

- 代码执行默认过 AST 白名单（禁文件/网络/子进程），整脚本闸门
- 连接仅本机回环（127.0.0.1:9876）
- 发行 zip 附 SSH 签名（ED25519），公钥在 `assets/release-signing/`
- 任何本地进程可绕过正式通道自起连接（架构已知面），详见 `references/11-deployment-security.md`
