# ComfyUI SSY Cloud Image Generator

一个强大的ComfyUI自定义节点集合，提供**4个专用节点**访问多个**SSY Cloud (胜算云)**同步图像生成和处理模型。

## 🌟 主要特性

### 四个专用节点

#### 🌟 SSY Google Generator
支持Google Gemini系列模型：
- **Google Gemini 2.5 Flash Image** - 最先进的多模态图像生成
- **Google Gemini 3 Pro Image** - 高级Gemini 3 Pro图像生成

#### 🎨 SSY Doubao Generator  
支持ByteDance Doubao系列模型：
- **Doubao SeeDream 4.5** - 最新字节豆包文生图和图生图
- **Doubao SeeDream 4.0** - 字节豆包文生图和图生图
- **Doubao SeeDream 3.0 T2I** - 专用文生图模型
- **Doubao SeedEdit 3.0 I2I** - 专用图生图模型

#### 🤖 SSY OpenAI Generator
支持OpenAI系列模型：
- **GPT Image 1** - OpenAI文生图生成

#### 🔧 SSY Bytedance Processor 火山引擎图片编辑节点
支持图像处理模型：
- **ByteDance Image Enhance** - AI驱动的图像增强
- **ByteDance Image Upscale** - 高质量图像放大

### 核心能力

✅ **专用节点设计** - 每个节点对应一个模型系列，参数清晰不混淆  
✅ **智能参数隔离** - 每个节点只显示其系列支持的参数  
✅ **安全的密钥管理** - API密钥密文显示，保护隐私  
✅ **精确的API适配** - 每个系列使用正确的API请求格式  
✅ **灵活的参数控制** - 控制尺寸、种子、步数、CFG比例等  
✅ **批量生成** - 一次请求生成多张图像  
✅ **多种格式支持** - 支持各种宽高比和输出格式  

## 📦 安装

1. 导航到你的ComfyUI自定义节点目录：
   ```bash
   cd ComfyUI/custom_nodes
   ```

2. 克隆此仓库：
   ```bash
   git clone https://github.com/SSYCloud/comfyui-nano-banana-ssy
   ```

3. 安装所需依赖：
   ```bash
   pip install -r requirements.txt
   ```

4. 重启ComfyUI

## 🔑 配置

### API密钥设置

你需要一个SSY Cloud API密钥来使用这些节点。从[胜算云](https://shengsuanyun.com)获取你的密钥。

**三种配置API密钥的方式：**

1. **在节点中** - 直接在`api_key`参数中输入（输入时自动显示为***）
2. **环境变量** - 设置`SSY_API_KEY`环境变量
3. **配置文件** - 首次使用后自动保存到`config.json`

**密钥安全性：**
- API密钥输入框使用密文显示（password字段）
- 输入时自动显示为`***`，保护隐私
- 首次输入后自动保存，后续无需重复输入

## 🎯 使用方法

### 1️⃣ SSY Google Generator 🌟

**支持模型：**
- `google/gemini-2.5-flash-image-preview`
- `google/gemini-3-pro-image-preview`

**参数说明：**
- **model** - 选择Gemini模型
- **prompt** - 生成提示词（必需）
- **input_image ~ input_image11** - 输入图像（最多12张，可选）
- **api_key** - API密钥（输入时显示为***）
- **aspect_ratio** - 生成图片比例（1:1、16:9等）
- **size** - 图像尺寸（1K/2K/4K，仅gemini-3-pro支持）
- **response_modalities** - 响应模态（IMAGE或TEXT_IMAGE）

**请求体格式（自动处理）：**
```json
{
  "model": "google/gemini-2.5-flash-image-preview",
  "prompt": "your prompt",
  "aspect_ratio": "1:1",
  "images": [{"inline_data": {"mime_type": "image/png", "data": "base64..."}}],
  "response_modalities": ["IMAGE"]
}
```

### 2️⃣ SSY Doubao Generator 🎨

**支持模型：**
- `bytedance/doubao-seedream-4.5`
- `bytedance/doubao-seedream-4-0`
- `bytedance/doubao-seedream-3.0-t2i`
- `bytedance/doubao-seededit-3-0-i2i`

**参数说明：**
- **model** - 选择Doubao模型
- **prompt** - 生成提示词（必需）
- **input_image ~ input_image9** - 输入图像（最多10张，可选）
- **api_key** - API密钥（输入时显示为***）
- **size** - 生成图片尺寸（1024x1024等）
- **n** - 生成图片数量（1-4）
- **quality** - 图像质量（standard/hd）
- **seed** - 随机种子（仅3.0系列支持）
- **guidance_scale** - CFG引导比例（仅3.0系列支持）
- **stream** - 流式输出（仅4.0/4.5系列支持）
- **sequential_image_generation** - 组图功能（仅4.0/4.5系列支持）
- **max_count** - 组图最大数量（仅4.0/4.5系列）
- **watermark** - 添加AI生成水印
- **response_format** - 返回格式（b64_json/url）

**请求体格式（自动处理）：**
```json
{
  "model": "bytedance/doubao-seedream-4.5",
  "prompt": "your prompt",
  "size": "1024x1024",
  "quality": "standard",
  "image": ["data:image/png;base64,..."],
  "stream": false,
  "sequential_image_generation": "auto",
  "sequential_image_generation_options": {"max_count": 4}
}
```

### 3️⃣ SSY OpenAI Generator 🤖

**支持模型：**
- `openai/gpt-image-1`

**参数说明：**
- **model** - 选择OpenAI模型
- **prompt** - 生成提示词（必需）
- **api_key** - API密钥（输入时显示为***）
- **size** - 生成图像尺寸（auto、1024x1024等）
- **n** - 生成图片数量（1-10）
- **quality** - 图像质量（auto/high/medium/low等）
- **background** - 背景透明度（auto/transparent/opaque）
- **output_format** - 输出格式（png/jpeg/webp）
- **output_compression** - 压缩级别（0-100）
- **moderation** - 内容审核级别（auto/low）

**请求体格式（自动处理）：**
```json
{
  "model": "openai/gpt-image-1",
  "prompt": "your prompt",
  "image": "data:image/png;base64,...",
  "n": 1,
  "size": "auto",
  "quality": "auto"
}
```

### 4️⃣ SSY Bytedance Processor 火山引擎图片编辑节点 🔧

**支持模型：**
- `bytedance/image_enhance` - 图像增强
- `bytedance/image_upscale` - 图像放大

**参数说明：**
- **model** - 选择处理模型
- **input_image** - 输入图像（必需）
- **api_key** - API密钥（输入时显示为***）
- **model_quality** - 超分模型质量（HQ/MQ/LQ，upscale必需）
- **resolution_boundary** - 目标分辨率（144p到2k）
- **jpg_quality** - JPG质量（0-100）
- **result_format** - 输出格式（0=png, 1=jpeg）

**请求体格式（自动处理）：**
```json
{
  "model": "openai/gpt-image-1",
  "prompt": "your prompt",
  "size": "1024x1024",
  "quality": "auto",
  "background": "transparent",
  "output_format": "png",
  "output_compression": 90,
  "moderation": "auto"
}
```
**请求体格式（自动处理）：**
```json
{
  "model": "bytedance/image_upscale",
  "binary_data_base64": ["base64..."],
  "model_quality": "MQ",
  "resolution_boundary": "1080p",
  "jpg_quality": 95,
  "result_format": 0,
  "return_url": true
}
```

## 📊 工作流示例

### 文生图（Google）
```
SSY Google Generator 🌟
├─ model: google/gemini-2.5-flash-image-preview
├─ prompt: "a beautiful sunset over mountains"
├─ aspect_ratio: 16:9
└─ response_modalities: IMAGE
```

### 图生图（Doubao）
```
Load Image → SSY Doubao Generator 🎨
              ├─ model: bytedance/doubao-seedream-4.5
              ├─ prompt: "transform into oil painting style"
              ├─ size: 1024x1024
              └─ quality: hd
```

### 图像放大
```
Load Image → SSY Bytedance Processor 🔧
              ├─ model: bytedance/image_upscale
              ├─ model_quality: HQ
              ├─ resolution_boundary: 2k
              └─ result_format: 0
```

## 🔄 模型能力对照表

| 节点 | 模型 | 文生图 | 图生图 | 特殊功能 |
|------|------|--------|--------|----------|
| Google 🌟 | Gemini 2.5 Flash | ✅ | ✅ | 多模态 |
| Google 🌟 | Gemini 3 Pro | ✅ | ✅ | 4K输出 |
| Doubao 🎨 | SeeDream 4.5 | ✅ | ✅ | 组图功能 |
| Doubao 🎨 | SeeDream 4.0 | ✅ | ✅ | 组图功能 |
| Doubao 🎨 | SeeDream 3.0 T2I | ✅ | - | 种子控制 |
| Doubao 🎨 | SeedEdit 3.0 I2I | - | ✅ | 种子控制 |
| OpenAI 🤖 | GPT Image 1 | ✅ | - | 透明背景 |
| Processor 🔧 | Image Enhance | - | - | AI增强 |
| Processor 🔧 | Image Upscale | - | - | 高清放大 |

## 🆕 版本更新

### v2.0 - 专用节点架构
- ✅ **4个专用节点** - 每个系列独立节点，参数清晰
- ✅ **API密钥密文显示** - 输入时显示为***，保护隐私安全
- ✅ **精确API适配** - 每个系列使用正确的请求格式
- ✅ **智能参数隔离** - 避免参数混淆和冲突
- ✅ **添加Doubao 4.5** - 支持最新模型
- ✅ **多图输入支持** - Google最多12张，Doubao最多10张

### 架构优势
1. **清晰的节点分类** - 在ComfyUI中按系列组织
2. **参数自动适配** - 选择节点后只显示相关参数
3. **代码模块化** - 易于维护和扩展
4. **类型安全** - 每个节点有明确的参数类型

## 🐛 故障排除

### 常见问题

**"未提供API密钥"**
- 确保在任一节点中设置了API密钥
- 密钥会自动保存供所有节点共享

**"模型需要输入图像"**
- 图生图模型（如SeedEdit 3.0 I2I）需要连接输入图像
- 图像处理节点必须提供输入图像

**"参数不生效"**
- 检查模型是否支持该参数
- 参数tooltip中会说明支持的模型版本

**"找不到节点"**
- 确保已重启ComfyUI
- 检查节点分类：SSY Cloud/Google、SSY Cloud/Doubao等

## 💡 使用技巧

1. **节点选择** - 根据需求选择对应系列节点
2. **参数优化** - 每个节点只显示相关参数，避免混淆
3. **工作流组织** - 可以在同一工作流中使用多个节点
4. **API密钥共享** - 所有节点共享同一个API密钥配置

## 📄 许可证

本项目采用MIT许可证 - 查看[LICENSE](LICENSE)文件获取详情。

## 🔗 链接

- [SSY Cloud官方网站](https://shengsuanyun.com)
- [API文档](https://shengsuanyun.com/docs)
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI)

## 🙏 致谢

为ComfyUI社区开发，提供专业的分类节点访问SSY Cloud强大的图像生成和处理模型。
