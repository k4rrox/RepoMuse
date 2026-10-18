<h1 align="center">RepoMuse</h1>

<p align="center"><strong>あなたのためだけに選ばれた GitHub プロジェクト。どれにも、エージェントが自ら作って試せるデモが付いています。</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <b>日本語</b>
</p>

<p align="center">
  <a href="https://github.com/k4rrox/RepoMuse/actions/workflows/ci.yml"><img src="https://github.com/k4rrox/RepoMuse/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-0f5132" alt="MIT license"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-0f5132" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/dependencies-0-0f5132" alt="依存関係ゼロ">
</p>

---

RepoMuse をコーディングエージェントに導入し、関心のあることを伝えてください。エージェントは決めた周期で GitHub を読み、
本当に時間をかける価値のある少数のプロジェクトだけを選び、**それぞれがなぜあなたに合うのか**を説明します。
触ってみるのが一番わかりやすいものについては、**実際のアップストリームのコードで小さなデモを作り**、ブラウザのタブで開けるようにします。
「役に立った」「興味なし」で評価すると、エージェントは次回の選定前にそれを読み込みます。

- **人気ではなく、あなた基準。** 選定は `profile.md` とフィードバックに基づき、スター数のランキングは使いません。
  何も選ばない回があっても問題ありません。
- **実際に試せるデモ。** 各デモはアップストリームのコミットを固定し、ネットワークに出られないサンドボックスで動き、
  何を検証し何を検証していないかを明記します（`ready`、`blocked`、`failed`）。
- **事実には必ずタイムスタンプ。** スター数は取得日時付きのスナップショットで、伸びの数字は出典の期間が明示されている場合のみ表示します。
  リンクはすべて HTTPS で、検証に通らないものは公開されません。
- **あえて小さく。** フレームワークもビルド手順もデータベースもありません。クローンすればすぐ動きます。

<p align="center">
  <img src="docs/images/picks.jpg" width="32%" alt="ピック一覧：左にフィルター、右に注目理由・主要技術・ライセンス・試しやすさを示すプロジェクトカード">
  <img src="docs/images/library.jpg" width="32%" alt="デモ一覧：すべての回の検証済みデモを、サムネイル・プロジェクト・技術とともに表示">
  <img src="docs/images/demo.jpg" width="32%" alt="デモ：本物の Taste Skill スキャナーがブラウザで動き、サンプルの横に結果を表示">
</p>

## 30 秒で試す

```bash
git clone https://github.com/k4rrox/RepoMuse && cd RepoMuse
./run.sh
```

http://127.0.0.1:53265/ を開くと、ラベル付きの**サンプルのピック**とサンプルのデモが 1 つ表示されます（デモはポート 53266 で動きます）。
Python 3.9 以上が必要です（macOS とほとんどの Linux には標準で入っています）。Windows では `python -m repomuse serve` を実行してください。
チャットのダイジェストでも時刻をタイムゾーンに変換したい場合は、任意で `pip install tzdata` を実行してください（ページ側は常に変換できます）。

## 自分用にする

エージェントでこのフォルダーを開き、こう伝えます。

> RepoMuse をセットアップして。

エージェントは [`skills/repomuse-setup`](skills/repomuse-setup/SKILL.md) に従い、最大 7 つの質問（関心分野、技術スタック、
見たくないもの、頻度、言語、デモを自発的に作ってよいか、ページとチャットのどちらで見るか）をしてから
`profile.md` と `repomuse.json` を作成し、定期実行の設定も提案します。その後はこう伝えるだけです。

> RepoMuse を実行して。 &nbsp;&nbsp;·&nbsp;&nbsp; 2 つ目のピックのデモを作って。

| エージェント | 指示の見つけ方 |
| --- | --- |
| Claude Code | リポジトリ内の `CLAUDE.md`。またはプラグインとして：`/plugin marketplace add k4rrox/RepoMuse` の後に `/plugin install repomuse@repomuse` |
| Codex、Cursor、Gemini CLI など | リポジトリ内の `AGENTS.md` が `skills/` の 3 つのスキルへ案内します |

ファイルを読み、GitHub を閲覧し、シェルコマンドを実行できるエージェントなら、どれでも動かせます。

## ページかチャットか

`repomuse.json` の `"mode"` で選びます。どちらのモードも同じピック・フィードバック・デモを共有するので、いつでも切り替えられます。

| | `"mode": "ui"`（既定） | `"mode": "no-ui"` |
| --- | --- | --- |
| ピック | フィルター・検索・デモ一覧付きのローカルページ（`./run.sh`） | エージェントがチャットに投稿する Markdown ダイジェスト（`repomuse digest`） |
| フィードバック | 「役に立った / 興味なし」ボタン | エージェントに「1 は役に立った、3 は興味なし」と伝える（`repomuse vote`） |
| デモ | カードの「デモを開く」 | `repomuse demo <slug>` がデモだけを配信し、ブラウザで開く |
| 常時起動 | ローカルサーバー | なし |

ダイジェストの例です（英語設定での実際の出力です。`language` を設定すると、あなたの言語で出力されます）。

```markdown
## RepoMuse · 2026-10-15 · 8 picks

### 4. [Taste Skill](https://github.com/Leonxlnx/taste-skill) · Worth trying
Let agents choose a visual direction for web pages, then check and fix it in a real browser

**Why now** The v2.0.0 rewrite shipped on October 13 at 14:05 Los Angeles time, adding scripts, a reference library and browser checks. Recent star growth not verified.
97,067 stars (2026-10-15 15:02) · MIT · Effort: Medium, needs setup
**Verified demo** Break "template look" into checkable details, then scan real code. Try it: `python3 -m repomuse demo taste-skill`
```

## デモの設定

`repomuse.json` の `demos` で、エージェントがどこまでデモを作るかを決めます。変えたいキーだけを書けば十分です。

```json
"demos": { "policy": "ask", "scope": "medium", "allow_installs": true, "max_per_run": 1 }
```

| キー | 値 |
| --- | --- |
| `policy` | `auto` 自分から作る · `ask`（既定）提案してから承認を待つ · `off` 作らない |
| `scope` | `small` 1 ページで 1 機能 · `medium`（既定）複数の操作、パッケージのバンドル可 · `large` より完全なシナリオ、重めのローカルビルド可 |
| `allow_installs` | `true`（既定）デモのフォルダー内でのパッケージのインストールを許可。`false` はそのまま動くファイルのみ |
| `max_per_run` | 1 回あたりのデモ数、0〜5（既定 1） |

`attach-demo` は `policy`、`max_per_run`、`allow_installs` を強制し、デモのスキルが各デモを `scope` の範囲に収めます。

## 仕組み

```text
profile.md + フィードバック ──▶ エージェントが repomuse-run ──▶ 公開（検証・マージ） ──▶ ページまたはダイジェスト
        ▲                           │                                                        │
        │                           └─▶ repomuse-demo ──▶ demos/<slug>/（サンドボックス） ─────┤
        └──────────────── 「役に立った」/「興味なし」 ◀──────────────────────────────────────┘
```

| 構成要素 | 役割 |
| --- | --- |
| `skills/` | 編集ルール：セットアップ、1 回の実行、1 つのデモ。どのエージェントでも従える Markdown。 |
| `repomuse/` | 標準ライブラリだけの Python：データ仕様、バリデーター、公開処理、ダイジェスト、ローカルサーバー、CLI。 |
| `web/` | ページ：HTML 1 つ、スタイルシート 1 つ、`web/js/` のネイティブ ES モジュール（ビルド不要）。 |
| `demos/radar-kit/` | すべてのデモが共有する、一覧へ戻るための上部バー。 |
| `docs/edition-format.md` | エージェントが書く全フィールドと、内容の正確さを保つルール。 |

### あなたのファイル

個人のデータはすべてリポジトリ内に保存され、**gitignore 済み**なので、`git pull` で更新しても衝突しません。

| ファイル | 書き込む人 | 内容 |
| --- | --- | --- |
| `profile.md` | あなたとエージェント | 見たいもの、見たくないもの、エージェントが気づいた好み |
| `repomuse.json` | セットアップ | タイトル、モード（`ui` / `no-ui`）、言語、タイムゾーン、周期、1 回あたりの件数、トピック、ポート、デモの設定 |
| `data/editions.json` | `publish` | すべての回 |
| `data/feedback.json` | ページまたは `vote` | あなたの「役に立った / 興味なし」 |
| `demos/<slug>/` | エージェント | 作成したデモ |
| `strings.json` | エージェント | あなたの言語での画面表示（任意、既定は英語） |

## コマンド

```bash
python3 -m repomuse serve [--port N]                  # ./run.sh と同じ
python3 -m repomuse init                              # repomuse.json と profile.md を作成
python3 -m repomuse check                             # 設定・データ・翻訳を検証
python3 -m repomuse publish FILE [--check] [--replace]
python3 -m repomuse attach-demo OWNER/REPO FILE [--check]
python3 -m repomuse feedback [--json]                 # フィードバックと対応するピックを一覧表示
python3 -m repomuse seen [--json]                     # これまでに選んだリポジトリを一覧表示
python3 -m repomuse digest [--day D] [--out F]        # no-ui：1 回分をチャット用の Markdown で出力
python3 -m repomuse vote OWNER/REPO like|dislike|clear [--reason R] [--note TEXT]
python3 -m repomuse demo [SLUG] [--no-open]           # no-ui：デモだけを配信して開く
python3 -m repomuse cover SLUG [--offset PX]          # ヘッドレス Chrome/Chromium/Edge でデモのサムネイルを作成
python3 -m repomuse migrate OLD.json                  # Open Source Radar からデータを移行
```

`publish` はリポジトリ単位でその日の回にマージします。同じ日に 2 回目を実行しても、上書きではなく追加になります。

## セキュリティモデル

- サーバーは `127.0.0.1` にだけバインドし、ローカルの `Host` ヘッダーのみを受け付け、厳格なコンテンツセキュリティポリシーを使います。
- デモは独立したオリジン（ページのポート + 1）で、`sandbox allow-scripts allow-same-origin` と `connect-src 'none'` のもとで動きます。
  ページのデータを読むことも API を呼ぶこともできず、ネットワークにも出られず、フォーム送信やポップアップもできません。
  配信するのはプレビュー用の資源だけで、`source/`、`src/`、`node_modules/`、README、設定ファイルは決して配信しません。
  （不透明なオリジンのサンドボックスではなく独立オリジンを使うのは、一部の組み込みブラウザーが不透明オリジンのページのサブリソースを
  一切読み込まないためです。）
- フィードバックの書き込みは同一オリジンの JSON だけを受け付けるため、他のサイトがあなたの代わりに投票することはできません。
- スキルはエージェントに対し、Web の内容を指示ではなくデータとして扱うこと、依存関係はデモのフォルダー内にのみインストールすること、
  認証情報を読まず、有料サービスを呼ばず、何もデプロイしないことを求めています。

脆弱性の報告方法は [SECURITY.md](SECURITY.md) をご覧ください。

## 開発

```bash
python3 -B -m unittest discover -s tests -v
for f in web/js/*.js; do node --check "$f"; done
node demos/taste-skill/source/upstream/lint.mjs web  # ページが従うスタイルルール
```

[CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。同梱のサンプルのピックは作者自身の実行結果で、ページ上でもサンプルと表示されます。

## ライセンス

[MIT](LICENSE)。同梱の `demos/taste-skill` には、それ自体の MIT ライセンスに従うアップストリームのコードが含まれます
（`demos/taste-skill/source/upstream/LICENSE`）。
