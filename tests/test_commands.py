from ai_daily.commands import handle_command


def test_generate_starts_tool_and_does_not_send():
    decision = handle_command("生成日报", generating=False, poster_ready=False)

    assert decision.reply == "好，我去做今天的日报啦"
    assert decision.start_tool is True
    assert decision.send is False


def test_generate_does_not_redo_when_poster_is_ready():
    decision = handle_command("生成日报", generating=False, poster_ready=True)

    assert decision.reply == "今天已经做好啦。要发到群里说发送，想重做说重新生成"
    assert decision.start_tool is False
    assert decision.send is False


def test_regenerate_starts_tool_even_when_poster_is_ready():
    decision = handle_command("重新生成", generating=False, poster_ready=True)

    assert decision.reply == "好，我去做今天的日报啦"
    assert decision.start_tool is True
    assert decision.send is False


def test_send_posts_webhook_only_when_poster_is_ready():
    ready = handle_command("发送", generating=False, poster_ready=True)
    missing = handle_command("发送", generating=False, poster_ready=False)

    assert ready.reply == "发到群里啦"
    assert ready.start_tool is False
    assert ready.send is True
    assert missing.reply == "今天还没有图呢。先说生成日报"
    assert missing.send is False
    assert missing.start_tool is False


def test_commands_wait_while_a_poster_is_being_made():
    for text in ("生成日报", "重新生成", "发送"):
        decision = handle_command(text, generating=True, poster_ready=False)

        assert decision.reply == "还在做呢，等我一下"
        assert decision.start_tool is False
        assert decision.send is False


def test_unknown_text_points_to_help_and_does_not_start():
    decision = handle_command("你好", generating=False, poster_ready=False)

    assert decision.reply == "「你好」我没听懂。发送「帮助」，我再告诉你。"
    assert decision.start_tool is False
    assert decision.send is False


def test_help_lists_each_command():
    decision = handle_command("帮助", generating=True, poster_ready=False)

    assert "生成日报" in decision.reply
    assert "重新生成" in decision.reply
    assert "发送" in decision.reply
    assert "时间 08:30" in decision.reply
    assert "参数" in decision.reply
    assert decision.start_tool is False
    assert decision.send is False


def test_extra_param_is_stored_as_one_pair():
    decision = handle_command(
        "参数 其他 size 1024x1024",
        generating=False,
        poster_ready=False,
    )

    assert decision.reply == "改好啦"
    assert decision.image_patch == {"size": "1024x1024"}
    assert decision.secret is None
    assert decision.start_tool is False
    assert decision.send is False


def test_bare_param_shows_model_and_address_but_not_the_secret():
    decision = handle_command(
        "参数",
        generating=False,
        poster_ready=False,
        image={"model": "gpt-image", "base_url": "https://img.example"},
        secret="sk-secret",
    )

    assert decision.reply == "gpt-image https://img.example"
    assert "sk-secret" not in decision.reply
    assert decision.image_patch is None
    assert decision.secret is None
    assert decision.start_tool is False
    assert decision.send is False


def test_base_url_is_saved_without_starting_the_tool():
    decision = handle_command(
        "参数 地址 https://img.example",
        generating=False,
        poster_ready=False,
    )

    assert decision.reply == "地址改好啦：https://img.example"
    assert decision.image_patch == {"base_url": "https://img.example"}
    assert decision.start_tool is False
    assert decision.send is False


def test_model_change_is_saved_and_named_in_the_reply():
    decision = handle_command("参数 模型 gpt-image", generating=True, poster_ready=False)

    assert decision.reply == "模型改好啦：gpt-image"
    assert decision.image_patch == {"model": "gpt-image"}
    assert decision.secret is None
    assert decision.start_tool is False


def test_valid_time_is_saved_and_does_not_start_the_tool():
    decision = handle_command("时间 08:30", generating=False, poster_ready=False)

    assert decision.reply == "好，提醒时间改成 08:30 啦"
    assert decision.schedule == "08:30"
    assert decision.start_tool is False
    assert decision.send is False


def test_bad_time_does_not_change_the_schedule():
    decision = handle_command("时间 25:99", generating=False, poster_ready=False)

    assert decision.schedule is None
    assert decision.start_tool is False
    assert decision.send is False
    assert decision.reply == "「时间 25:99」我没听懂。发送「帮助」，我再告诉你。"


def test_secret_is_saved_apart_from_the_reply():
    decision = handle_command(
        "参数 密钥 sk-secret",
        generating=True,
        poster_ready=False,
    )

    assert decision.reply == "改好啦"
    assert "sk-secret" not in decision.reply
    assert decision.secret == "sk-secret"
    assert decision.image_patch is None
    assert decision.start_tool is False
    assert decision.send is False
