import os
import gradio as gr
import openai


openai.api_base = os.environ.get("OPENAI_API_BASE")
openai.api_key = os.environ.get("OPENAI_API_KEY")
MODEL_TYPE = os.environ.get("MODEL_TYPE")


def make_prediction(history, max_tokens=None, temperature=None, top_p=None):
    messages = []
    for idx, (user, bot) in enumerate(history):
        messages.append({"role": "user", "content": user})
        if idx != len(history) - 1:
            messages.append({"role": "assistant", "content": bot})

    # print(messages)

    completion = openai.ChatCompletion.create(model=MODEL_TYPE, messages=messages, max_tokens=max_tokens, temperature=temperature, top_p=top_p, stream=True)
    for chunk in completion:
        content = chunk["choices"][0]["delta"].get("content", "")
        if content:
            yield content


def clear_chat(chat_history_state, chat_message):
    chat_history_state = []
    chat_message = ''
    return chat_history_state, chat_message


def user(message, history):
    history = history or []
    # Append the user's message to the conversation history
    history.append([message, ""])
    return "", history


def chat(history, max_tokens, temperature, top_p):
    history = history or []

    prediction = make_prediction(
        history,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p
    )

    for delta_text in prediction:
        history[-1][1] += delta_text
        # stream the response
        yield history, history, ""


start_message = ""

with gr.Blocks() as demo:
    with gr.Tab("Chatbot"):
        gr.Markdown("# 🎇 OpenChat 3.5 Playground 💬 ")
        chatbot = gr.Chatbot().style(height=500)
        with gr.Row():
            message = gr.Textbox(
                label="What do you want to chat about?",
                placeholder="Ask me anything.",
                lines=3,
            )
        with gr.Row():
            submit = gr.Button(value="Send message", variant="secondary").style(full_width=True)
            clear = gr.Button(value="New topic", variant="secondary").style(full_width=False)
            stop = gr.Button(value="Stop", variant="secondary").style(full_width=False)
        with gr.Row():
            with gr.Column():
                max_tokens = gr.Slider(32, 4096, label="Max Tokens", step=32, value=1024)
                temperature = gr.Slider(0.0, 1.0, label="Temperature", step=0.1, value=0.5)
                top_p = gr.Slider(0.0, 1.0, label="Top P", step=0.05, value=1.0)

        chat_history_state = gr.State()
        clear.click(clear_chat, inputs=[chat_history_state, message], outputs=[chat_history_state, message], queue=False)
        clear.click(lambda: None, None, chatbot, queue=False)

        submit_click_event = submit.click(
            fn=user, inputs=[message, chat_history_state], outputs=[message, chat_history_state], queue=True
        ).then(
            fn=chat, inputs=[chat_history_state, max_tokens, temperature, top_p], outputs=[chat_history_state, chatbot, message], queue=True
        )
        stop.click(fn=None, inputs=None, outputs=None, cancels=[submit_click_event], queue=False)

demo.queue(max_size=128, concurrency_count=48).launch(debug=True, server_name="0.0.0.0", server_port=7860)
