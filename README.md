# Clipbot GTA VI — clipa, legenda e posta sozinho (GitHub Actions, grátis)

A cada hora o GitHub Actions: vê se algum canal da lista está ao vivo → grava ~40 min →
acha os melhores momentos (picos de áudio + chat da Twitch) → corta em 9:16 com fundo desfocado →
legenda automática (Whisper local) → título + hashtags → publica no YouTube Shorts, TikTok e Instagram Reels →
manda o clipe pronto no seu Telegram.

## Setup (uns 15 min)
1. Crie um repositório **público** no GitHub (público = minutos grátis ilimitados) e suba esta pasta.
2. Edite `config.yml`: cole só os **links** dos canais (Twitch/Kick/YouTube) e ajuste hashtags.
3. Em *Settings → Secrets and variables → Actions*, crie os secrets abaixo (só os das plataformas que for usar).
4. Aba *Actions* → `clipbot` → *Run workflow* → marque **test** (modo teste: grava 4 min de um canal ao vivo, gera 1 clipe sempre e manda só pro Telegram). Se esse teste chegar no seu Telegram, o pipeline todo funciona. Depois roda sozinho toda hora.

### Telegram (plano B garantido, faça primeiro)
Crie um bot com o @BotFather → `TG_BOT_TOKEN`. Mande uma mensagem pro bot e pegue seu id
em `https://api.telegram.org/bot<TOKEN>/getUpdates` → `TG_CHAT_ID`.
Cada clipe pronto chega no seu celular, pronto pra postar em 10 segundos.

### YouTube Shorts
Google Cloud Console → crie projeto → ative *YouTube Data API v3* → credencial OAuth (Desktop) → baixe o JSON.
Rode no PC: `python scripts/get_youtube_token.py client_secret.json` e copie para os secrets:
`YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.

### TikTok
developers.tiktok.com → crie app → produto *Content Posting API* (Direct Post) → faça o OAuth (escopo `video.publish`)
e guarde: `TT_CLIENT_KEY`, `TT_CLIENT_SECRET`, `TT_REFRESH_TOKEN`.

### Instagram Reels
Requisitos: conta Instagram **Profissional** (Criador/Empresa) ligada a uma Página do Facebook.
1. developers.facebook.com → criar app (tipo *Business*) → adicionar o produto *Instagram* com *Facebook Login for Business*.
2. Permissões: `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`.
3. No *Graph API Explorer* gere um token de usuário com essas permissões e troque por um token de longa duração (60 dias).
4. Pegue o ID da conta Instagram (`GET /me/accounts` → `GET /{page-id}?fields=instagram_business_account`).
5. Secrets: `IG_USER_ID` e `IG_ACCESS_TOKEN`. O token de 60 dias precisa ser renovado (anote no calendário).
Com sua própria conta e o app em modo de desenvolvimento, normalmente dá pra testar sem App Review. Confirme na hora.
O upload é resumável (sem URL pública). Versão da API: variável `IG_GRAPH_VERSION` (padrão v24.0), se a Meta aposentar, troque.

## LIMITES IMPORTANTES (leia)
- **Apps não auditados postam como privado**: TikTok (`SELF_ONLY`) e YouTube (vídeo travado em privado) só liberam
  publicação pública depois da auditoria do app. Até lá, use o Telegram para postar com 1 toque, ou peça a auditoria.
  Variáveis `YT_PRIVACY` e `TT_PRIVACY` (Settings → Variables) controlam isso.
- YouTube API grátis: ~6 uploads/dia (`max_posts_per_day`).
- Instagram: token dura ~60 dias (renovar), limite de publicações da API por dia, e para outras contas além da sua é preciso App Review (semanas).
- Kick depende do plugin do streamlink funcionar na versão instalada; chat só é lido na Twitch (nos outros usa só áudio).
- Cobre ~40 de cada 60 min de uma live, não 24h. Aumente `record_minutes` (máx ~50) se quiser.
- **Direitos autorais/monetização**: clipar lives de terceiros sem permissão pode dar strike e as plataformas
  tendem a não monetizar conteúdo reaproveitado. Peça autorização ao streamer e credite sempre (o bot já coloca o nome do canal).
- Não testei contra Twitch/Kick/TikTok/YouTube reais (sem acesso daqui): testei detecção, corte 9:16 e legenda
  num vídeo sintético. Rode o primeiro *Run workflow* e me mande o log se algo falhar.
