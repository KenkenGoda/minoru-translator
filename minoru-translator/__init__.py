import os
import re

import azure.functions as func
import slack_sdk
import openai


def summarize(message: str) -> str:
    response = openai.Completion.create(
        engine="gpt-35-turbo-v0301",
        prompt=f"小学生がわかるように要約してください:\n\n{message}",
        max_tokens=512,
        temperature=0.2
    )
    return str(response.choices[0].text)

def translate_to_gal(message: str) -> str:
    example_content = """
        ギャル語は、若者たちの間で使われる日本のスラングです。絵文字や顔文字を使ってコミュニケーションすることが一般的です。以下にいくつかの例文を記載します。

        「昨日のパーリー、マジヤバかったわー(笑)🎉💖 またやりたいね✌️😆」
        「あの服、超キュートじゃん💕👗 オシャレ度アゲアゲだね✨」
        「彼とのデート、超楽しかった(〃ω〃)💓 もっと一緒にいたかったなぁ〜😣」
        「今日のランチ、めっちゃ美味しかった！🍱🤤 また行きたいなぁ( ˘ω˘ )」
        「明日は一緒にショッピング🛍️💄 行くのがマジ楽しみだわー(≧▽≦)」
        「友達とカラオケ行ってきた♬ 最高に盛り上がったわ( *´艸｀)🎤」

        ギャル語は、独特の言い回しや単語を使うことで、若者たちの仲間意識を高めています。絵文字や顔文字を使って表現力豊かに会話を楽しむことが一般的です。
    """
    response = openai.ChatCompletion.create(
        engine="gpt-35-turbo-v0301",
        messages=[
            {
                "role": "system",
                "content": example_content
            },
            {
                "role": "user",
                "content": f"次の文章を例文に従ってギャル語に変換してください:\n\n{message}"
            }
        ],
        max_tokens=1024,
        temperature=0.7
    )
    return str(response.choices[0].message.content)

def main(req: func.HttpRequest) -> func.HttpResponse:
    # SlackAppを使えるようにするためのおまじない
    # challengeならそれをそのまま返す
    challenge = req.get_json().get('challenge')
    if challenge:
        return func.HttpResponse(challenge, status_code=200)
    if "x-slack-retry-num" in req.headers and req.headers["x-slack-retry-reason"] == "http_timeout":
        return func.HttpResponse("Retry", status_code=200)

    # slackのeventを取得
    message = req.get_json().get('event').get('text')
    # messageから、先頭のメンション文字列(<@~~~~~~~~~>)を正規表現で取り除く
    message = re.sub(r'<@.*?>', '', message)
    # channel_id
    channel_id = req.get_json().get('event').get('channel')

    # openaiの設定
    openai.api_type = "azure"
    openai.api_base = os.getenv("OPENAI_API_BASE")
    openai.api_version = os.getenv("OPENAI_API_VERSION")
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # 文章を要約
    message = summarize(message)

    # 文章をギャル風に翻訳
    message = translate_to_gal(message)

    # slackへの返信
    slack_oauth_token = os.getenv("SLACK_API_TOKEN")
    slack_client = slack_sdk.WebClient(token=slack_oauth_token)
    slack_client.chat_postMessage(channel=channel_id, text=message)

    return func.HttpResponse("OK", status_code=200)
