# AI_streamer

ローカルLLM (Ollama) を使って、Twitchチャットに反応したり、チャットが静かなときは自分で話題を作ったり深掘りしたりして喋り続けるAI配信ボットです。音声合成にはVOICEVOXを使用します。

## 特徴

- Twitchチャットのメッセージに反応して短く返答
- チャットが一定時間 (`idle_seconds`) 無いときは、直前の話題を深掘りして話し続ける
- 深掘りが `max_deep_dives` 回続いたら、自分から新しい話題に切り替える
- 会話履歴を保持してLLMに渡す (直近 `history_max_messages` 件)
- VOICEVOXでテキストを音声合成し、ローカルで再生 (OBSの音声入力等にルーティングして配信可能)
- Twitchチャットにも返答テキストを投稿

## 事前準備

1. **Python 3.10以上**
2. **[Ollama](https://ollama.com/)** をインストールし、使いたいモデルをpull
   ```
   ollama pull llama3
   ollama serve
   ```
3. **[VOICEVOX](https://voicevox.hiroshiba.jp/)** エンジンを起動 (デフォルトで `http://127.0.0.1:50021`)
4. **Twitch Botアカウント**を用意し、OAuthトークンを取得
   ([twitchtokengenerator.com](https://twitchtokengenerator.com/) 等)
5. (Linuxのみ) 音声再生に `sounddevice` が使うPortAudioが必要
   ```
   sudo apt install portaudio19-dev
   ```

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env を編集して TWITCH_TOKEN / TWITCH_CHANNEL / TWITCH_BOT_NICK を設定
```

`config.yaml` で以下を調整できます。

- `llm.model` / `llm.host`: 使用するOllamaモデルとホスト
- `tts.enabled` / `tts.voicevox_host` / `tts.speaker_id`: 音声合成の設定 (`enabled: false` でTTSを無効化しテキストのみ)
- `persona.system_prompt`: キャラクター設定・口調
- `behavior.idle_seconds`: チャットが無いときに自発発話するまでの秒数
- `behavior.max_deep_dives`: 同じ話題を深掘りする最大連続回数
- `behavior.history_max_messages`: LLMに渡す会話履歴の最大件数

## 起動

```bash
python -m src.main
```

## テスト

会話ロジック (`src/conversation.py`) はLLM/Twitch/TTSをモックしたユニットテストでカバーしています。

```bash
pip install -r requirements-dev.txt
pytest
```

## 構成

```
src/
  config.py          # .env / config.yaml の読み込み
  conversation.py     # 中核ロジック: チャット反応・深掘り・自発話題のステートマシン
  twitch_bot.py        # Twitchチャットの送受信アダプタ (TwitchIO)
  llm/ollama_client.py # Ollamaへの会話生成リクエスト
  tts/voicevox_client.py # VOICEVOXへの音声合成リクエスト
  tts/audio_player.py   # 合成音声のローカル再生
  main.py              # 各コンポーネントを配線してbotを起動
```

## 今後の拡張候補

- VTube Studio等と連携したアバター/リップシンク制御
- 配信ゲーム画面や実況コメントの取り込み (視覚情報を話題に反映)
- クラウドLLM/TTSへの切り替え対応
