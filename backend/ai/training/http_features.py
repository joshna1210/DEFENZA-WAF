import re
import urllib.parse


def extract_features(method: str, url: str, body: str = ""):
    """
    Extract structural HTTP request features for the DEFENZA XGBoost model.

    These features are intentionally based on request structure and
    suspicious patterns rather than raw request text.
    """

    # ---------------------------------------------------------
    # Normalize inputs
    # ---------------------------------------------------------
    method = str(method or "").upper()
    url = str(url or "")
    body = str(body or "")

    raw = url + " " + body

    # URL decoding
    decoded = urllib.parse.unquote(raw)
    double_decoded = urllib.parse.unquote(decoded)

    # Extract path without query string
    path = url.split("?", 1)[0]

    # ---------------------------------------------------------
    # Feature extraction
    # ---------------------------------------------------------
    features = {

        # =====================================================
        # LENGTH FEATURES
        # =====================================================
        "url_length": len(url),
        "body_length": len(body),
        "total_length": len(raw),

        # =====================================================
        # URL STRUCTURE
        # =====================================================
        "parameter_count": url.count("&") + (1 if "?" in url else 0),

        "path_depth": len(
            [segment for segment in path.split("/") if segment]
        ),

        # =====================================================
        # SPECIAL CHARACTER FEATURES
        # =====================================================
        "quote_count": (
            raw.count("'")
            + raw.count('"')
        ),

        "semicolon_count": raw.count(";"),

        "pipe_count": raw.count("|"),

        "ampersand_count": raw.count("&"),

        "equals_count": raw.count("="),

        "angle_bracket_count": (
            raw.count("<")
            + raw.count(">")
        ),

        "parentheses_count": (
            raw.count("(")
            + raw.count(")")
        ),

        "brace_count": (
            raw.count("{")
            + raw.count("}")
        ),

        "bracket_count": (
            raw.count("[")
            + raw.count("]")
        ),

        "backslash_count": raw.count("\\"),

        # =====================================================
        # ENCODING FEATURES
        # =====================================================
        "percent_encoded_count": len(
            re.findall(
                r"%[0-9a-fA-F]{2}",
                raw
            )
        ),

        "double_encoded_count": len(
            re.findall(
                r"%25[0-9a-fA-F]{2}",
                raw
            )
        ),

        # =====================================================
        # PATH TRAVERSAL FEATURES
        # =====================================================
        "traversal_count": (
            raw.lower().count("../")
        ),

        "decoded_traversal_count": (
            decoded.lower().count("../")
        ),

        "double_decoded_traversal_count": (
            double_decoded.lower().count("../")
        ),

        # =====================================================
        # SQL INJECTION FEATURES
        # =====================================================
        "sql_keyword_count": len(
            re.findall(
                r"\b("
                r"select|"
                r"union|"
                r"insert|"
                r"update|"
                r"delete|"
                r"drop|"
                r"alter|"
                r"create|"
                r"from|"
                r"where|"
                r"or|"
                r"and"
                r")\b",
                raw,
                re.IGNORECASE,
            )
        ),

        "sql_comment_count": (
            raw.count("--")
            + raw.count("/*")
            + raw.count("*/")
            + raw.count("#")
        ),

        # =====================================================
        # XSS FEATURES
        # =====================================================
        "xss_keyword_count": len(
            re.findall(
                r"(script|"
                r"javascript:|"
                r"onerror|"
                r"onload|"
                r"onclick|"
                r"iframe|"
                r"svg)",
                raw,
                re.IGNORECASE,
            )
        ),

        # =====================================================
        # COMMAND INJECTION FEATURES
        # NOTE:
        # 'id' intentionally excluded because normal URLs
        # commonly contain ?id=25
        # =====================================================
        "command_keyword_count": len(
            re.findall(
                r"\b("
                r"whoami|"
                r"uname|"
                r"cat|"
                r"ls|"
                r"pwd|"
                r"wget|"
                r"curl|"
                r"bash|"
                r"sh|"
                r"cmd|"
                r"powershell|"
                r"nc"
                r")\b",
                raw,
                re.IGNORECASE,
            )
        ),

        "shell_operator_count": (
            raw.count(";")
            + raw.count("|")
            + raw.count("&&")
            + raw.count("||")
            + raw.count("`")
        ),

        # =====================================================
        # CHARACTER COMPOSITION
        # =====================================================
        "digit_count": sum(
            character.isdigit()
            for character in raw
        ),

        "alpha_count": sum(
            character.isalpha()
            for character in raw
        ),

        "special_count": sum(
            not character.isalnum()
            and not character.isspace()
            for character in raw
        ),
    }

    # ---------------------------------------------------------
    # Character ratios
    # ---------------------------------------------------------
    total = max(len(raw), 1)

    features["digit_ratio"] = (
        features["digit_count"] / total
    )

    features["alpha_ratio"] = (
        features["alpha_count"] / total
    )

    features["special_ratio"] = (
        features["special_count"] / total
    )

    # ---------------------------------------------------------
    # HTTP method flags
    # ---------------------------------------------------------
    for http_method in [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
    ]:
        features[
            f"method_{http_method.lower()}"
        ] = int(method == http_method)

    return features


# =============================================================
# LOCAL TEST
# =============================================================

if __name__ == "__main__":

    examples = [

        # Benign
        (
            "GET",
            "/products?id=25",
            ""
        ),

        # SQL Injection
        (
            "GET",
            "/products?id=1 OR 1=1",
            ""
        ),

        # XSS
        (
            "GET",
            "/search?q=<script>alert(1)</script>",
            ""
        ),

        # Path Traversal
        (
            "GET",
            "/download?file=../../../../etc/passwd",
            ""
        ),

        # Command Injection
        (
            "GET",
            "/ping?host=127.0.0.1;whoami",
            ""
        ),
    ]

    for method, url, body in examples:

        print("\n" + "=" * 70)
        print("REQUEST:")
        print(f"{method} {url}")

        print("\nFEATURES:")

        extracted = extract_features(
            method,
            url,
            body
        )

        for feature_name, feature_value in extracted.items():
            print(
                f"{feature_name:35} : "
                f"{feature_value}"
            )