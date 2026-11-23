# X folks

**本文3行で答えを完結させ、根拠だけを後ろに置く**文章校正Skillです。成功・失敗・未完了の理由を本文に含め、読者が「なぜ？」と聞き返す原因を減らします。

## 仕様

- 本文は1〜3行、1行80文字以内。結論・理由・必要な条件を残し、回答を別資料へ逃がしません。
- 根拠欄は本文の引用ではなく、資料が裏付ける対象の短い要約を使います。
- 同名ファイルは区別できる短いパスで表示します。Codexではインラインコード、Markdown対応環境では短い表示名付きリンクを使います。
- Python 3の標準ライブラリだけで形式を検査できます。PythonなしでもSkillの自己点検指示は機能します。

## 導入

リポジトリのルートで実行します。Windowsの作業ディレクトリ例は `C:\work\x-folks` です。

~~~powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
New-Item -ItemType Junction -Path "$HOME\.agents\skills\x-folks" -Target (Resolve-Path ".\skills\x-folks")
~~~

macOS・Linuxの場合：

~~~sh
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/skills/x-folks" "$HOME/.agents/skills/x-folks"
~~~

期待結果は共通Skill配置先の `x-folks/SKILL.md` と `x-folks/scripts/validate.py` を参照できる状態です。既存の同名Skillを確認せず上書きしないでください。追加後は新しいセッションで呼び出します。

## 監査

入力JSONは `candidate.json` などの名前で保存します。次は出力形式を示す架空の例です。

~~~json
{
  "lines": [
    "日本語化のため2 MODの翻訳を追加し、全キーの一致を確認しました。",
    "画面取得ツールが対象を検出できず、実機検証は未実施です。",
    "GitHubの認証情報を取得できず、コミット済みですがプッシュは未完了です。"
  ],
  "evidence": [
    {"summary": "翻訳追加ファイル", "lines": [1], "refs": ["assets/mod-a/lang/ja_jp.json:1", "assets/mod-b/lang/ja_jp.json:1"]},
    {"summary": "画面検証失敗の記録", "lines": [2], "refs": ["logs/game-check.txt:1"]},
    {"summary": "Git認証失敗の記録", "lines": [3], "refs": ["logs/push.txt:1"]}
  ]
}
~~~

Windows（`C:\work\x-folks` から実行）：

~~~powershell
py -3 skills\x-folks\scripts\validate.py candidate.json
~~~

macOS・Linux（リポジトリのルートから実行）：

~~~sh
python3 skills/x-folks/scripts/validate.py candidate.json
~~~

終了コード0は合格で、標準出力に本文と根拠欄だけが出ます。形式違反は1、入力エラーは2です。標準入力も利用できます。既定の表示形式はCodex用で、ファイル参照を `mod-a/lang/ja_jp.json:1` のようなインラインコードにします。JSONに `"style": "markdown"` を追加すると `[mod-a/lang/ja_jp.json](assets/mod-a/lang/ja_jp.json#L1)` 形式のリンクを生成します。実際のクリック可否は利用するクライアントによります。

テストはWindowsの `C:\work\x-folks` で `py -3 -m unittest discover -s tests -v`、macOS・Linuxでは同じルートで `python3 -m unittest discover -s tests -v` を実行します。成功時は最後に `OK` と表示されます。

## 制約

スクリプトが検査できるのは行数・文字数・根拠ラベル・参照形式・行番号です。**理由の妥当性、回答漏れ、資料の実在・意味的な一致、リンクの動作は保証しません。** これらはLLM側で回答前に確認する必要があります。Skill単体には全環境の送信を止める共通機能はありません。

MITライセンスで公開しています。
