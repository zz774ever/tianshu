# FlagTree 0.7 四轮测试完整输入与输出

容器：`test_plugin_28`；日期：2026-11-05。20 个原始场景，共 104 条请求。

本页保留全部题目和模型回答，不截断。原始 API 响应、usage、检查和耗时另见每节链接的 JSON；图片使用原始本地路径。没有保存完整服务终端日志，终端诊断只有单独的观察记录。

## Qwen3.6-27B-eager / image_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_concurrent_8.json)

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 30.201,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 30.202,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 26.092,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.739,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Does this image contain visible text? Reply yes or no."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "yes"
  ]
}
````

完整回答：

````text
yes
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 19.839,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 1050,
    "total_tokens": 1052,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-06

完整输入：

````json
{
  "request_id": "image-06",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What shape is inside the red circle? Reply with the shape name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png",
  "required_terms": [
    "square"
  ]
}
````

完整回答：

````text
square
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.732,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-07

完整输入：

````json
{
  "request_id": "image-07",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What color is the triangle? Reply with the color name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png",
  "required_terms": [
    "yellow"
  ]
}
````

完整回答：

````text
yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.735,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 187,
    "total_tokens": 189,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-08

完整输入：

````json
{
  "request_id": "image-08",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many blue circles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png",
  "required_terms": [
    "4"
  ]
}
````

完整回答：

````text
4
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.737,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-eager / image_single

[完整原始 JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/image_single.json)

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Read the two words. The second word has four letters. Copy every visible character exactly and reply with the text only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "hello",
    "vllm"
  ]
}
````

完整回答：

````text
HELLO
VLLM
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 16.327,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 7,
    "prompt_tokens": 1062,
    "total_tokens": 1069,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-eager / mixed_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/mixed_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 8.101,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 8.316,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 8.322,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 8.318,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 32.403,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 32.403,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 31.035,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 8.313,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-eager / text_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 26.305,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 25.628,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 25.633,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 25.633,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-05

完整输入：

````json
{
  "request_id": "text-05",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the chemical formula for water. Reply with the formula only."
    }
  ],
  "required_terms": [
    "h2o"
  ]
}
````

完整回答：

````text
H₂O
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 30.636,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 4,
    "prompt_tokens": 25,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-06

完整输入：

````json
{
  "request_id": "text-06",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name Earth's largest ocean. Reply with the ocean name only."
    }
  ],
  "required_terms": [
    "pacific"
  ]
}
````

完整回答：

````text
Pacific Ocean
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 26.303,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 25,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-07

完整输入：

````json
{
  "request_id": "text-07",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 5 multiplied by 6. Reply with the number only."
    }
  ],
  "required_terms": [
    "30"
  ]
}
````

完整回答：

````text
30
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 26.297,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 26,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-08

完整输入：

````json
{
  "request_id": "text-08",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "What color results from mixing blue and yellow paint? Reply with one word."
    }
  ],
  "required_terms": [
    "green"
  ]
}
````

完整回答：

````text
Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 25.628,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 27,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-eager / text_single

[完整原始 JSON](results/Qwen3.6-27B-eager/Qwen3.6-27B/port-8132/text_single.json)

### text-llm-details

完整输入：

````json
{
  "request_id": "text-llm-details",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Introduce large language models (LLMs) in detail. Explain what they are, how training and inference work, typical capabilities, limitations, and responsible use. Write a coherent response of at least 256 characters. Do not repeat words or phrases unnecessarily."
    }
  ],
  "required_terms": [
    "large language model",
    "training",
    "inference",
    "limitations"
  ],
  "min_length": 256,
  "max_tokens": 512
}
````

完整回答：

````text
Large language models are advanced artificial intelligence systems trained on vast datasets to understand and generate human-like text. They operate using deep learning architectures, primarily transformers, which allow them to process sequential data efficiently. During training, these models learn statistical patterns and relationships between words by predicting the next token in a sequence. This process requires immense computational power and diverse data sources to capture linguistic nuances, factual knowledge, and reasoning abilities.

Inference involves the model generating responses to user prompts based on its learned parameters. When a user inputs text, the model calculates probabilities for subsequent tokens, selecting the most likely continuation to form coherent output. Typical capabilities include natural language understanding, translation, summarization, coding assistance, and creative writing. These systems excel at pattern recognition and can adapt to various contexts without explicit reprogramming for each task.

However, LLMs possess significant limitations. They may produce hallucinations, presenting false information with high confidence. Their knowledge is static, limited to their training cutoff date, and they lack true understanding or consciousness. Bias present in training data can lead to unfair or harmful outputs. Therefore, responsible use is critical. Developers and users must implement robust safety measures, such as content filtering and human oversight, to mitigate risks. Transparency about the model's nature and limitations helps manage expectations. Ethical deployment requires continuous monitoring for bias, ensuring privacy protection, and preventing misuse in malicious activities. By acknowledging these constraints and adhering to ethical guidelines, society can harness the transformative potential of LLMs while minimizing adverse impacts. This balanced approach fosters innovation and trust in AI technologies, enabling beneficial applications across healthcare, education, and industry.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 243.571,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 328,
    "prompt_tokens": 65,
    "total_tokens": 393,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-graph / image_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_concurrent_8.json)

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 15.017,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 15.114,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 15.017,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.159,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Does this image contain visible text? Reply yes or no."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "yes"
  ]
}
````

完整回答：

````text
yes
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.206,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 1050,
    "total_tokens": 1052,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-06

完整输入：

````json
{
  "request_id": "image-06",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What shape is inside the red circle? Reply with the shape name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png",
  "required_terms": [
    "square"
  ]
}
````

完整回答：

````text
square
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.153,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-07

完整输入：

````json
{
  "request_id": "image-07",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What color is the triangle? Reply with the color name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png",
  "required_terms": [
    "yellow"
  ]
}
````

完整回答：

````text
yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.159,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 187,
    "total_tokens": 189,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-08

完整输入：

````json
{
  "request_id": "image-08",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many blue circles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png",
  "required_terms": [
    "4"
  ]
}
````

完整回答：

````text
4
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.157,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-graph / image_single

[完整原始 JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/image_single.json)

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Read the two words. The second word has four letters. Copy every visible character exactly and reply with the text only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "hello",
    "vllm"
  ]
}
````

完整回答：

````text
HELLO
VLLM
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 11.684,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 7,
    "prompt_tokens": 1062,
    "total_tokens": 1069,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-graph / mixed_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/mixed_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 22.864,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 2.979,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 22.419,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 22.415,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 23.502,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 23.503,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 22.779,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 22.412,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-graph / text_concurrent_8

[完整原始 JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 13.86,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.464,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.462,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.464,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-05

完整输入：

````json
{
  "request_id": "text-05",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the chemical formula for water. Reply with the formula only."
    }
  ],
  "required_terms": [
    "h2o"
  ]
}
````

完整回答：

````text
H₂O
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.199,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 4,
    "prompt_tokens": 25,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-06

完整输入：

````json
{
  "request_id": "text-06",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name Earth's largest ocean. Reply with the ocean name only."
    }
  ],
  "required_terms": [
    "pacific"
  ]
}
````

完整回答：

````text
Pacific Ocean
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 16.215,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 25,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-07

完整输入：

````json
{
  "request_id": "text-07",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 5 multiplied by 6. Reply with the number only."
    }
  ],
  "required_terms": [
    "30"
  ]
}
````

完整回答：

````text
30
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 16.211,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 26,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-08

完整输入：

````json
{
  "request_id": "text-08",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "What color results from mixing blue and yellow paint? Reply with one word."
    }
  ],
  "required_terms": [
    "green"
  ]
}
````

完整回答：

````text
Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.455,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 27,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-27B-graph / text_single

[完整原始 JSON](results/Qwen3.6-27B-graph/Qwen3.6-27B/port-8132/text_single.json)

### text-llm-details

完整输入：

````json
{
  "request_id": "text-llm-details",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Introduce large language models (LLMs) in detail. Explain what they are, how training and inference work, typical capabilities, limitations, and responsible use. Write a coherent response of at least 256 characters. Do not repeat words or phrases unnecessarily."
    }
  ],
  "required_terms": [
    "large language model",
    "training",
    "inference",
    "limitations"
  ],
  "min_length": 256,
  "max_tokens": 512
}
````

完整回答：

````text
Large language models are advanced artificial intelligence systems trained on vast datasets to understand and generate human-like text. They operate using deep learning architectures, primarily transformers, which allow them to process sequential data efficiently. During training, these models learn statistical patterns and relationships between words by predicting the next token in a sequence. This process requires immense computational power and diverse data sources to capture linguistic nuances, factual knowledge, and reasoning abilities.

Inference involves the model generating responses to user prompts based on its learned parameters. When a user inputs text, the model calculates probabilities for subsequent tokens, selecting the most likely continuation to form coherent output. Typical capabilities include natural language understanding, translation, summarization, coding assistance, and creative writing. These systems excel at pattern recognition and can adapt to various contexts without explicit reprogramming for each task.

However, LLMs possess significant limitations. They may produce hallucinations, presenting false information with high confidence. Their knowledge is static, limited to their training cutoff date, and they lack true understanding or consciousness. Bias present in training data can lead to unfair or harmful outputs. Therefore, responsible use is critical. Developers and users must implement robust safety measures, such as content filtering and human oversight, to mitigate risks. Transparency about the model's nature and limitations helps manage expectations. Ethical deployment requires continuous monitoring for bias, ensuring privacy protection, and preventing misuse in malicious activities. By acknowledging these constraints and adhering to ethical guidelines, society can harness the transformative potential of LLMs while minimizing adverse impacts. This balanced approach fosters innovation and trust in AI technologies, enabling beneficial applications across healthcare, education, and industry.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 32.281,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 328,
    "prompt_tokens": 65,
    "total_tokens": 393,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-eager / image_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json)

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 27.619,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 27.615,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 25.204,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 18.901,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Does this image contain visible text? Reply yes or no."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "yes"
  ]
}
````

完整回答：

````text
Yes.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 19.952,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 1050,
    "total_tokens": 1053,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-06

完整输入：

````json
{
  "request_id": "image-06",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What shape is inside the red circle? Reply with the shape name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png",
  "required_terms": [
    "square"
  ]
}
````

完整回答：

````text
square
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 18.893,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-07

完整输入：

````json
{
  "request_id": "image-07",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What color is the triangle? Reply with the color name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png",
  "required_terms": [
    "yellow"
  ]
}
````

完整回答：

````text
yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 18.896,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 187,
    "total_tokens": 189,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-08

完整输入：

````json
{
  "request_id": "image-08",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many blue circles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png",
  "required_terms": [
    "4"
  ]
}
````

完整回答：

````text
4
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 18.897,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-eager / image_single

[完整原始 JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/image_single.json)

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Read the two words. The second word has four letters. Copy every visible character exactly and reply with the text only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "hello",
    "vllm"
  ]
}
````

完整回答：

````text
HELLO
VLLM
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.868,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 7,
    "prompt_tokens": 1062,
    "total_tokens": 1069,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-eager / mixed_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 49.598,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 49.708,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 49.702,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 49.188,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 53.546,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 53.542,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 52.368,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 49.697,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-eager / text_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.937,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.411,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.412,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.404,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-05

完整输入：

````json
{
  "request_id": "text-05",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the chemical formula for water. Reply with the formula only."
    }
  ],
  "required_terms": [
    "h2o"
  ]
}
````

完整回答：

````text
H₂O
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 23.939,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 4,
    "prompt_tokens": 25,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-06

完整输入：

````json
{
  "request_id": "text-06",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name Earth's largest ocean. Reply with the ocean name only."
    }
  ],
  "required_terms": [
    "pacific"
  ]
}
````

完整回答：

````text
Pacific Ocean
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.939,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 25,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-07

完整输入：

````json
{
  "request_id": "text-07",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 5 multiplied by 6. Reply with the number only."
    }
  ],
  "required_terms": [
    "30"
  ]
}
````

完整回答：

````text
30
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.937,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 26,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-08

完整输入：

````json
{
  "request_id": "text-08",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "What color results from mixing blue and yellow paint? Reply with one word."
    }
  ],
  "required_terms": [
    "green"
  ]
}
````

完整回答：

````text
 Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 21.406,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 27,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-eager / text_single

[完整原始 JSON](results/Qwen3.6-35B-A3B-eager/Qwen3.6-35B-A3B/port-8132/text_single.json)

### text-llm-details

完整输入：

````json
{
  "request_id": "text-llm-details",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Introduce large language models (LLMs) in detail. Explain what they are, how training and inference work, typical capabilities, limitations, and responsible use. Write a coherent response of at least 256 characters. Do not repeat words or phrases unnecessarily."
    }
  ],
  "required_terms": [
    "large language model",
    "training",
    "inference",
    "limitations"
  ],
  "min_length": 256,
  "max_tokens": 512
}
````

完整回答：

````text
Large language models (LLMs) are advanced artificial intelligence systems trained on vast datasets to understand and generate human-like text. These models rely on transformer architectures, utilizing self-attention mechanisms to process sequential data efficiently. Training involves two primary phases: pre-training on massive, diverse text corpora to learn general language patterns, followed by fine-tuning on specific tasks or alignment with human preferences to improve safety and utility. During inference, the model processes user prompts to predict the most likely subsequent tokens, generating coherent and relevant responses. Capabilities include natural language understanding, creative writing, code generation, and complex reasoning. However, limitations exist, such as hallucinations, bias, and lack of true understanding. Responsible use requires careful oversight, transparency, and adherence to ethical guidelines to mitigate risks and ensure beneficial outcomes for society.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 106.952,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 163,
    "prompt_tokens": 65,
    "total_tokens": 228,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-graph / image_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_concurrent_8.json)

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 40.196,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 40.134,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 40.131,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 39.952,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Does this image contain visible text? Reply yes or no."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "yes"
  ]
}
````

完整回答：

````text
Yes.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 40.053,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 1050,
    "total_tokens": 1053,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-06

完整输入：

````json
{
  "request_id": "image-06",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What shape is inside the red circle? Reply with the shape name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_06.png",
  "required_terms": [
    "square"
  ]
}
````

完整回答：

````text
square
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 39.958,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-07

完整输入：

````json
{
  "request_id": "image-07",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What color is the triangle? Reply with the color name only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_07.png",
  "required_terms": [
    "yellow"
  ]
}
````

完整回答：

````text
yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 39.955,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 187,
    "total_tokens": 189,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-08

完整输入：

````json
{
  "request_id": "image-08",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many blue circles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_08.png",
  "required_terms": [
    "4"
  ]
}
````

完整回答：

````text
4
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 39.953,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 189,
    "total_tokens": 191,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-graph / image_single

[完整原始 JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/image_single.json)

### image-05

完整输入：

````json
{
  "request_id": "image-05",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Read the two words. The second word has four letters. Copy every visible character exactly and reply with the text only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_05.png",
  "required_terms": [
    "hello",
    "vllm"
  ]
}
````

完整回答：

````text
HELLO
VLLM
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 14.547,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 7,
    "prompt_tokens": 1062,
    "total_tokens": 1069,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-graph / mixed_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/mixed_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 18.117,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.74,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.735,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.738,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-01

完整输入：

````json
{
  "request_id": "image-01",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_01.png",
  "required_terms": [
    "red",
    "green",
    "blue",
    "yellow"
  ]
}
````

完整回答：

````text
Red, Green, Blue, Yellow
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.983,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-02

完整输入：

````json
{
  "request_id": "image-02",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the four quadrant colors in this order: top-left, top-right, bottom-left, bottom-right. Reply with color names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_02.png",
  "required_terms": [
    "blue",
    "yellow",
    "red",
    "green"
  ]
}
````

完整回答：

````text
Blue, Yellow, Red, Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.98,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 8,
    "prompt_tokens": 201,
    "total_tokens": 209,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-03

完整输入：

````json
{
  "request_id": "image-03",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Name the three shapes from left to right. Reply with shape names only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_03.png",
  "required_terms": [
    "circle",
    "square",
    "triangle"
  ]
}
````

完整回答：

````text
Circle, Square, Triangle
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.891,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 6,
    "prompt_tokens": 189,
    "total_tokens": 195,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### image-04

完整输入：

````json
{
  "request_id": "image-04",
  "kind": "image",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "How many triangles are in the image? Reply with the number only."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "file:///workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png"
          }
        }
      ]
    }
  ],
  "image_path": "/workspace/vllm-plugin-FL/tools/adaptation-gate-cases/images/image_04.png",
  "required_terms": [
    "3"
  ]
}
````

完整回答：

````text
3
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 17.735,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 188,
    "total_tokens": 190,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-graph / text_concurrent_8

[完整原始 JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_concurrent_8.json)

### text-01

完整输入：

````json
{
  "request_id": "text-01",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 19 + 23. Reply with the number only."
    }
  ],
  "required_terms": [
    "42"
  ]
}
````

完整回答：

````text
42
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.379,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 27,
    "total_tokens": 30,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-02

完整输入：

````json
{
  "request_id": "text-02",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name the capital of France. Reply with the city only."
    }
  ],
  "required_terms": [
    "paris"
  ]
}
````

完整回答：

````text
Paris
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.375,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 24,
    "total_tokens": 26,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-03

完整输入：

````json
{
  "request_id": "text-03",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the opposite of hot. Reply with one word."
    }
  ],
  "required_terms": [
    "cold"
  ]
}
````

完整回答：

````text
Cold
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.449,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 23,
    "total_tokens": 25,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-04

完整输入：

````json
{
  "request_id": "text-04",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "How many days are in one week? Reply with the number only."
    }
  ],
  "required_terms": [
    "7"
  ]
}
````

完整回答：

````text
7
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.453,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 26,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-05

完整输入：

````json
{
  "request_id": "text-05",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Give the chemical formula for water. Reply with the formula only."
    }
  ],
  "required_terms": [
    "h2o"
  ]
}
````

完整回答：

````text
H₂O
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 43.064,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 4,
    "prompt_tokens": 25,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-06

完整输入：

````json
{
  "request_id": "text-06",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Name Earth's largest ocean. Reply with the ocean name only."
    }
  ],
  "required_terms": [
    "pacific"
  ]
}
````

完整回答：

````text
Pacific Ocean
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.843,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 25,
    "total_tokens": 28,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-07

完整输入：

````json
{
  "request_id": "text-07",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Compute 5 multiplied by 6. Reply with the number only."
    }
  ],
  "required_terms": [
    "30"
  ]
}
````

完整回答：

````text
30
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.844,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 3,
    "prompt_tokens": 26,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

### text-08

完整输入：

````json
{
  "request_id": "text-08",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "What color results from mixing blue and yellow paint? Reply with one word."
    }
  ],
  "required_terms": [
    "green"
  ]
}
````

完整回答：

````text
 Green
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 42.448,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 2,
    "prompt_tokens": 27,
    "total_tokens": 29,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````

## Qwen3.6-35B-A3B-graph / text_single

[完整原始 JSON](results/Qwen3.6-35B-A3B-graph/Qwen3.6-35B-A3B/port-8132/text_single.json)

### text-llm-details

完整输入：

````json
{
  "request_id": "text-llm-details",
  "kind": "text",
  "messages": [
    {
      "role": "user",
      "content": "Introduce large language models (LLMs) in detail. Explain what they are, how training and inference work, typical capabilities, limitations, and responsible use. Write a coherent response of at least 256 characters. Do not repeat words or phrases unnecessarily."
    }
  ],
  "required_terms": [
    "large language model",
    "training",
    "inference",
    "limitations"
  ],
  "min_length": 256,
  "max_tokens": 512
}
````

完整回答：

````text
Large language models (LLMs) are advanced artificial intelligence systems trained on vast datasets to understand and generate human-like text. These models rely on transformer architectures, utilizing self-attention mechanisms to process sequential data efficiently. Training involves pre-training on massive corpora to learn general language patterns, followed by fine-tuning on specific tasks or reinforcement learning from human feedback to align outputs with user intent. During inference, the model predicts the next token in a sequence based on the provided context, enabling capabilities such as natural language understanding, creative writing, code generation, and complex reasoning. Despite their impressive abilities, LLMs face significant limitations, including hallucinations where they generate false information, biases inherited from training data, and high computational costs. To ensure responsible use, developers and users must implement robust safety guardrails, verify factual accuracy, and address ethical concerns regarding privacy and intellectual property. Understanding these dynamics is crucial for leveraging LLMs effectively while mitigating potential risks in various applications.
````

检查与响应统计：

````json
{
  "passed": true,
  "latency_seconds": 16.653,
  "checks": {
    "non_empty": true,
    "minimum_length": true,
    "expected_semantics": true,
    "expected_order": true,
    "no_bang_triplet": true,
    "no_mojibake": true,
    "no_control_characters": true,
    "no_long_character_run": true,
    "no_repeated_word_run": true,
    "no_repeated_phrase": true
  },
  "finish_reason": "stop",
  "usage": {
    "completion_tokens": 195,
    "prompt_tokens": 65,
    "total_tokens": 260,
    "completion_tokens_details": null,
    "prompt_tokens_details": null
  }
}
````
