<h1 align="center">RepoMuse</h1>

<p align="center"><strong>为你量身挑选的 GitHub 项目精选，每个项目都附带你的 Agent 亲手做好、可以直接试用的 Demo。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <a href="https://github.com/k4rrox/RepoMuse/actions/workflows/ci.yml"><img src="https://github.com/k4rrox/RepoMuse/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f5132" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-0f5132" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/dependencies-0-0f5132" alt="零依赖">
</p>

---

把 RepoMuse 装进你的编程 Agent，告诉它你关心什么。它会按你设定的周期替你阅读 GitHub，只挑出少数真正值得花时间的项目，
说明**每个项目为什么适合你**；对那些"上手一试就懂"的项目，它还会**基于真实的上游代码做一个小 Demo**，你在浏览器标签页里就能打开。
你把精选标记为"有用"或"不想看"，Agent 在下一次挑选前会读取这些反馈。

- **按你的口味，而不是按热度。** 精选依据你的 `profile.md` 和反馈，从不按 Star 排名。一期没有推荐也是合理的。
- **能真正试用的 Demo。** 每个 Demo 都固定了上游 commit，在沙箱中运行、不能联网，并写清楚验证过什么、没验证什么
  （`ready`、`blocked` 或 `failed`）。
- **事实都带时间戳。** Star 数是带采集时间的快照，增长数据只在注明来源窗口时才显示，所有链接都是 HTTPS，
  校验不通过就不会发布。
- **刻意保持小巧。** 没有框架、没有构建步骤、没有数据库，克隆下来就能运行。

<p align="center">
  <img src="docs/images/picks.jpg" width="32%" alt="精选页面：左侧是筛选，右侧是项目卡片，包含为什么关注、核心技术栈、许可证和试用门槛">
  <img src="docs/images/library.jpg" width="32%" alt="Demo 库：汇总所有期中已验证的 Demo，带封面、所属项目和技术栈">
  <img src="docs/images/demo.jpg" width="32%" alt="Demo：真实的 Taste Skill 扫描器在浏览器中运行，旁边是扫描结果">
</p>

## 30 秒体验

```bash
git clone https://github.com/k4rrox/RepoMuse && cd RepoMuse
./run.sh
```

打开它打印出的地址，你会看到带有标注的**示例精选**和一个示例 Demo。
需要 Python 3.9+（macOS 和大多数 Linux 已自带）。在 Windows 上请运行 `python -m repomuse serve`；可选执行
`pip install tzdata`，让对话摘要也能把时间转换到你的时区（网页始终可以）。

## 变成你自己的

在你的 Agent 中打开这个文件夹，然后说：

> 帮我设置 RepoMuse。

Agent 会按照 [`skills/repomuse-setup`](skills/repomuse-setup/SKILL.md) 操作：最多问你七个问题（关注方向、技术栈、不想看什么、
频率、语言、是否允许它主动做 Demo、在网页还是在对话里看），写好 `profile.md` 和 `repomuse.json`，并主动提出帮你设置定时运行。之后你可以说：

> 跑一期 RepoMuse。 &nbsp;&nbsp;·&nbsp;&nbsp; 给第二个项目做个 Demo。

| Agent | 如何找到指令 |
| --- | --- |
| Claude Code | 仓库里的 `CLAUDE.md`；或作为插件安装：`/plugin marketplace add k4rrox/RepoMuse`，然后 `/plugin install repomuse@repomuse` |
| Codex、Cursor、Gemini CLI 等 | 仓库里的 `AGENTS.md` 会指向 `skills/` 中的三个 Skill |

只要 Agent 能读文件、能访问 GitHub、能运行 Shell 命令，就能驱动 RepoMuse。

## 网页模式或对话模式

在 `repomuse.json` 中设置 `"mode"`。两种模式共用同一份精选、反馈和 Demo，随时可以切换。

| | `"mode": "ui"`（默认） | `"mode": "no-ui"` |
| --- | --- | --- |
| 看精选 | 本地网页，带筛选、搜索和 Demo 库（`./run.sh`） | Agent 在对话中发出的 Markdown 摘要（`repomuse digest`） |
| 给反馈 | 点击"有用 / 不想看"按钮 | 对 Agent 说"1 有用，3 不想看"（`repomuse vote`） |
| 看 Demo | 卡片上的"打开 Demo" | `repomuse demo <slug>` 只启动 Demo 服务，并在浏览器中打开 |
| 需要常驻运行 | 本地服务 | 无 |

摘要示例如下（这是英文配置下的真实输出；设置 `language` 后，摘要会使用你的语言）：

```markdown
## RepoMuse · 2026-10-15 · 8 picks

### 4. [Taste Skill](https://github.com/Leonxlnx/taste-skill) · Worth trying
Let agents choose a visual direction for web pages, then check and fix it in a real browser

**Why now** The v2.0.0 rewrite shipped on October 13 at 14:05 Los Angeles time, adding scripts, a reference library and browser checks. Recent star growth not verified.
97,067 stars (2026-10-15 15:02) · MIT · Effort: Medium, needs setup
**Verified demo** Break "template look" into checkable details, then scan real code. Try it: `python3 -m repomuse demo taste-skill`
```

## Demo 设置

`repomuse.json` 里的 `demos` 决定 Agent 做 Demo 能做到什么程度。只需写你想改的字段。

```json
"demos": { "policy": "ask", "scope": "medium", "allow_installs": true, "max_per_run": 1 }
```

| 字段 | 取值 |
| --- | --- |
| `policy` | `auto` 主动做 · `ask`（默认）先提出、等你同意再做 · `off` 不做 |
| `scope` | `small` 一个页面、一个功能 · `medium`（默认）多步交互，可以打包依赖 · `large` 更完整的场景，允许较重的本地构建 |
| `allow_installs` | `true`（默认）允许在 Demo 目录内安装依赖；`false` 只允许无需安装就能运行的文件 |
| `max_per_run` | 每期最多几个 Demo，0–5（默认 1） |

`attach-demo` 会强制检查 `policy`、`max_per_run` 和 `allow_installs`；Demo Skill 负责把每个 Demo 控制在 `scope` 之内。

## 工作原理

```text
profile.md + 反馈 ──▶ Agent 运行 repomuse-run ──▶ 发布（校验、合并） ──▶ 网页或对话摘要
        ▲                  │                                                    │
        │                  └─▶ repomuse-demo ──▶ demos/<slug>/（沙箱） ───────────┤
        └──────────────── "有用" / "不想看" ◀────────────────────────────────────┘
```

| 组成部分 | 作用 |
| --- | --- |
| `skills/` | 编辑规则：初始化、跑一期、做一个 Demo。任何 Agent 都能照着执行的 Markdown。 |
| `repomuse/` | 只用标准库的 Python：数据契约、校验器、发布器、摘要、本地服务、命令行。 |
| `web/` | 页面：一个 HTML、一个样式表，以及 `web/js/` 中的原生 ES 模块（无需构建）。 |
| `demos/radar-kit/` | 所有 Demo 共用的顶栏，用于返回 Demo 库。 |
| `docs/edition-format.md` | Agent 写入的每个字段，以及保证内容真实的规则。 |

### 你的文件

所有个人数据都保存在仓库目录里，并且**已加入 gitignore**，所以 `git pull` 更新时不会冲突：

| 文件 | 由谁写入 | 内容 |
| --- | --- | --- |
| `profile.md` | 你和 Agent | 关注什么、不想看什么、Agent 观察到的偏好 |
| `repomuse.json` | 初始化 | 标题、模式（`ui` / `no-ui`）、语言、时区、周期、每期数量、方向、端口（可选）、Demo 设置 |
| `data/editions.json` | `publish` | 所有精选期数 |
| `data/feedback.json` | 网页或 `vote` | 你的"有用 / 不想看" |
| `demos/<slug>/` | Agent | 它做好的 Demo |
| `strings.json` | Agent | 界面的本地化文案（可选，默认英文） |

## 命令

```bash
python3 -m repomuse serve [--port N]                  # 等同于 ./run.sh
python3 -m repomuse status [--json]                   # 页面和 Demo 运行在哪里
python3 -m repomuse init                              # 创建 repomuse.json 和 profile.md
python3 -m repomuse check                             # 校验配置、数据和翻译
python3 -m repomuse publish FILE [--check] [--replace]
python3 -m repomuse attach-demo OWNER/REPO FILE [--check]
python3 -m repomuse feedback [--json]                 # 列出反馈及对应的精选
python3 -m repomuse seen [--json]                     # 列出所有已推荐过的仓库
python3 -m repomuse digest [--day D] [--out F]        # no-ui：把一期精选输出为对话用的 Markdown
python3 -m repomuse vote OWNER/REPO like|dislike|clear [--reason R] [--note TEXT]
python3 -m repomuse demo [SLUG] [--no-open]           # no-ui：只启动 Demo 服务并打开
python3 -m repomuse cover SLUG [--offset PX]          # 用无头 Chrome/Chromium/Edge 生成 Demo 封面
python3 -m repomuse migrate OLD.json                  # 从 Open Source Radar 升级数据
```

`publish` 会按仓库合并到当天：同一天第二次运行会追加内容，而不是覆盖。

## 安全模型

- 服务只绑定 `127.0.0.1`，只接受本机的 `Host` 请求头，并使用严格的内容安全策略（CSP）。
- Demo 运行在独立的来源上（单独的端口），并设置 `sandbox allow-scripts allow-same-origin` 和 `connect-src 'none'`：
  它们读不到页面数据、调用不了页面接口、无法联网，也不能提交表单或打开弹窗。服务只提供预览资源，
  `source/`、`src/`、`node_modules/`、README 和配置文件一律不会对外提供。（之所以用独立来源，而不是无来源的沙箱，
  是因为部分内嵌浏览器会拒绝加载无来源页面的任何子资源。）
- 写入反馈只接受同源的 JSON 请求，其他网站无法替你投票。
- Skill 要求 Agent 把网页内容视为数据而不是指令，只在 Demo 目录内安装依赖，不读取凭据、不调用付费服务、不对外部署。

漏洞报告方式见 [SECURITY.md](SECURITY.md)。

## 开发

```bash
python3 -B -m unittest discover -s tests -v
for f in web/js/*.js; do node --check "$f"; done
node demos/taste-skill/source/upstream/lint.mjs web  # 页面遵循的样式规则
```

参见 [CONTRIBUTING.md](CONTRIBUTING.md)。随附的示例精选来自作者自己的运行结果，并在页面上标注为示例。

## 许可证

[MIT](LICENSE)。随附的 `demos/taste-skill` 包含遵循其自身 MIT 许可证的上游代码，见
`demos/taste-skill/source/upstream/LICENSE`。
