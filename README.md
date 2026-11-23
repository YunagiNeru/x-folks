# X folks

**本文3行で答えを完結させ、根拠だけを後ろに置く**文章校正Skillです。X向けの極短文を求められたとき、LLMに結論・条件・数値を優先させます。

## 特徴

- 本文は1〜3行、1行80文字以内。資料への丸投げや根拠欄への説明逃げを禁止します。
- 本文に書いた発言と、実在するファイル位置・URLを対応付けます。
- Python 3の標準ライブラリだけで形式を検査します。Pythonがなくても指示文による自己点検は可能です。

## 導入

リポジトリの作業ディレクトリから、Skillフォルダを利用するエージェントのSkill配置先にコピーまたはリンクしてください。Codexのユーザー共通配置先の例は、Windowsで `$HOME\.agents\skills\x-folks`、macOSとLinuxで `~/.agents/skills/x-folks` です。

Windows（PowerShell、作業ディレクトリはリポジトリのルート）:

~~~powershell
New-Item -ItemType Directory -Force "$HOME\.agents\skills"
New-Item -ItemType Junction -Path "$HOME\.agents\skills\x-folks" -Target (Resolve-Path ".\skills\x-folks")
~~~

macOS・Linux（作業ディレクトリはリポジトリのルート）:

~~~sh
mkdir -p "$HOME/.agents/skills"
ln -s "$(pwd)/skills/x-folks" "$HOME/.agents/skills/x-folks"
~~~

配置先に同名のSkillがある場合は、既存の内容を確認してから入れ替えてください。新しいセッションでSkillを明示的に呼び出すと動作確認できます。

## 監査の使い方

作業ディレクトリ: リポジトリのルート。入力ファイル: `candidate.json`。以下は形式の例であり、架空の出典を事実確認済みと扱わないでください。

~~~json
{
  "lines": ["結論A。", "条件B。"],
  "evidence": [
    {"claims": ["結論A", "条件B"], "refs": ["src/main.py:12-18", "https://example.org/spec"]}
  ]
}
~~~

Windows:

~~~powershell
py -3 skills\x-folks\scripts\validate.py candidate.json
~~~

macOS・Linux:

~~~sh
python3 skills/x-folks/scripts/validate.py candidate.json
~~~

合格時は終了コード0で、標準出力に**本文と根拠欄だけ**が出ます。不合格時は終了コード1、入力エラーは2です。スクリプトは標準入力も受け付けるため、候補ファイルを残す必要はありません。

テスト: リポジトリのルートで `py -3 -m unittest discover -s tests -v`（Windows）、または `python3 -m unittest discover -s tests -v` を実行します。成功時は全テストが `OK` で終了します。

## 保証範囲

スクリプトが検査するのは文字数・行数・JSON形式・出典の記述形式・発言との文字列対応です。回答の完全性、情報の真偽、資料の内容との一致、画面幅による折り返しは保証しません。Skill単体には、全プラットフォームの回答送信を強制的に遮断する共通機能はありません。機械監査を実行できない環境では指示文に従って自己点検します。

MITライセンスで公開します。