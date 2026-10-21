from ai_daily.aihot import clean_source

def test_clean_source_drops_a_trailing_parenthetical():
    assert clean_source("Inception Labs：Blog（网页）") == "Inception Labs：Blog"
    assert clean_source("公众号：DeepSeek（深度求索）") == "公众号：DeepSeek"
    assert clean_source("X：ChatGPT (@ChatGPT)") == "X：ChatGPT"
