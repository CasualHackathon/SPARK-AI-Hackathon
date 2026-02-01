# 创建一个 utils/test_assertions.py 文件，封装所有常用断言逻辑为一个类

class AgentTestAssertions:
    @staticmethod
    def assert_keywords_in_response(response: str, query: str, keywords: list[str]):
        """
        通用断言：响应必须包含指定关键词之一。
        """
        assert response is not None, f"Query `{query}` returned None!"
        assert isinstance(response, str), f"Query `{query}` did not return a string! Got {type(response)}"
        assert len(response.strip()) > 0, f"Query `{query}` returned an empty string!"
        for kw in keywords:
            assert kw.lower() in response.lower(), f"Expected keyword `{kw}` not found in response: {response}"

    @staticmethod
    def assert_response_matches_exact(response: str, query: str, expected: str):
        """
        精准匹配响应的字符串结果（适用于数值等）。
        """
        assert response is not None, f"Query `{query}` returned None"
        assert isinstance(response, str), f"Query `{query}` returned a non-string: {type(response)}"
        assert expected in response.replace(",", ""), f"Expected result '{expected}' not found in response: {response}"

    @staticmethod
    def assert_response_not_empty(response: str, query: str):
        """
        检查响应非空且为字符串。
        """
        assert response is not None, f"Query `{query}` returned None!"
        assert isinstance(response, str), f"Query `{query}` did not return a string!"
        assert len(response.strip()) > 0, f"Query `{query}` returned an empty string!"
