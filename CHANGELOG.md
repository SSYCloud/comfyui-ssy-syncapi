# 更新日志

## [2.0.0] - 2024-12-05

### 🎉 主要重构 - 专用节点架构

这是一个重大版本更新，将单个统一节点重构为**4个专用节点**，每个节点对应一个模型系列，实现真正的参数隔离和智能适配。

### ✨ 新增功能

#### 4个专用节点
- **SSY Google Generator 🌟** - Google Gemini系列专用节点
  - `google/gemini-2.5-flash-image-preview`
  - `google/gemini-3-pro-image-preview`
  
- **SSY Doubao Generator 🎨** - ByteDance Doubao系列专用节点
  - `bytedance/doubao-seedream-4.5` ⭐ 新增
  - `bytedance/doubao-seedream-4-0`
  - `bytedance/doubao-seedream-3.0-t2i`
  - `bytedance/doubao-seededit-3-0-i2i`
  
- **SSY OpenAI Generator 🤖** - OpenAI系列专用节点
  - `openai/gpt-image-1`
  
- **SSY Image Processor 🔧** - 图像处理专用节点
  - `bytedance/image_enhance`
  - `bytedance/image_upscale`

#### 核心改进
- **智能参数隔离**
  - 每个节点只显示其系列支持的参数
  - 避免参数混淆和错误配置
  - 用户界面更清晰简洁
  
- **API密钥密文显示**
  - 所有节点的API密钥输入使用`password: True`
  - 在ComfyUI界面显示为`••••••`
  - 保护用户隐私和安全性
  
- **新增Doubao 4.5模型**
  - 支持最新的`bytedance/doubao-seedream-4.5`模型
  - 包含所有4.0系列的功能
  - 支持组图功能和多图输入

### 🔧 技术改进

#### 精确的API请求构建
每个节点使用正确的API格式：

**Google系列：**
```json
{
  "model": "google/gemini-2.5-flash-image-preview",
  "images": [{"inline_data": {"mime_type": "image/png", "data": "..."}}],
  "aspect_ratio": "1:1",
  "response_modalities": ["IMAGE"]
}
```

**Doubao系列：**
```json
{
  "model": "bytedance/doubao-seedream-4.5",
  "image": ["data:image/png;base64,..."],
  "size": "1024x1024",
  "sequential_image_generation": "auto"
}
```

**OpenAI系列：**
```json
{
  "model": "openai/gpt-image-1",
  "size": "1024x1024",
  "background": "transparent",
  "output_format": "png"
}
```

**图像处理系列：**
```json
{
  "model": "bytedance/image_upscale",
  "binary_data_base64": ["..."],
  "model_quality": "MQ",
  "resolution_boundary": "1080p"
}
```

#### 代码架构
- **基础类抽象** - `SSYAPIBase`提供公共功能
- **模块化设计** - 每个节点独立实现
- **易于扩展** - 添加新模型只需扩展对应节点
- **类型安全** - 明确的参数类型定义

### 🔄 变更

#### 从v1.0迁移
- **旧版本**：1个统一节点 `ComfyUI_NanoBanana`
- **新版本**：4个专用节点，按系列分类

#### 节点映射
| v1.0 | v2.0 |
|------|------|
| 选择Google模型 | 使用 SSY Google Generator 🌟 |
| 选择Doubao模型 | 使用 SSY Doubao Generator 🎨 |
| 选择OpenAI模型 | 使用 SSY OpenAI Generator 🤖 |
| 选择处理模型 | 使用 SSY Image Processor 🔧 |

#### 参数变化
- **移除通用前缀** - 不再需要`google_`、`doubao_`等前缀
- **直接命名** - 每个节点的参数直接使用原始名称
- **清晰分类** - 在ComfyUI中按`SSY Cloud/`分类显示

### 📝 文档更新

- **完全重写README.md** - 详细介绍4个节点的使用
- **添加请求体示例** - 展示每个系列的API格式
- **更新工作流示例** - 展示不同节点的组合使用
- **添加迁移指南** - 帮助v1.0用户升级

### 🐛 修复

- ✅ 修复了不同模型系列使用错误API参数格式的问题
- ✅ 修复了参数混淆导致的生成失败
- ✅ 改进了错误处理和日志输出
- ✅ 修复了图像格式转换的兼容性问题

### 🔐 安全性

- ✅ API密钥密文显示（`password: True`）
- ✅ 改进了密钥验证逻辑
- ✅ 更安全的配置文件管理
- ✅ 所有节点共享密钥配置

### ⚡ 性能优化

- 优化了图像转换流程
- 减少了不必要的参数传递
- 改进了API响应解析
- 更快的节点加载速度

### 🎯 用户体验

- **清晰的节点选择** - 根据需求直接选择对应节点
- **简洁的参数面板** - 只显示相关参数
- **明确的功能分类** - 在ComfyUI中易于找到
- **Emoji标识** - 🌟🎨🤖🔧 快速识别节点类型

### 📊 架构优势

1. **参数隔离** - 避免不同系列参数互相干扰
2. **易于维护** - 每个节点独立，修改不影响其他节点
3. **扩展性强** - 添加新模型只需修改对应节点
4. **类型安全** - 每个节点有明确的输入输出类型
5. **代码复用** - 通过基础类共享公共功能

---

## [1.0.0] - 初始版本

### 特性

- 支持多个SSY Cloud模型（统一节点）
- 基础的图像生成和处理功能
- 通用参数接口
- 模型选择下拉框
- 所有参数在一个节点中

### 限制

- 参数混杂，不同系列的参数都显示
- 容易配置错误的参数组合
- API格式适配不够精确
- 用户界面较为复杂
