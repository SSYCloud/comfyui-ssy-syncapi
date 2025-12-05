import os
import json
import base64
import requests
from io import BytesIO
from PIL import Image
import torch
import numpy as np

p = os.path.dirname(os.path.realpath(__file__))

def get_config():
    try:
        config_path = os.path.join(p, 'config.json')
        with open(config_path, 'r') as f:  
            config = json.load(f)
        return config
    except:
        return {}

def save_config(config):
    config_path = os.path.join(p, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

class SSYAPIBase:
    """SSY Cloud API基础类"""
    
    def __init__(self):
        env_key = os.environ.get("SSY_API_KEY")
        placeholders = {"token_here", "place_token_here", "your_api_key",
                        "api_key_here", "enter_your_key", "<api_key>"}

        if env_key and env_key.lower().strip() not in placeholders:
            self.api_key = env_key
        else:
            config = get_config()
            self.api_key = config.get("SSY_API_KEY")

    def tensor_to_image(self, tensor):
        """Convert tensor to PIL Image"""
        tensor = tensor.cpu()
        if len(tensor.shape) == 4:
            tensor = tensor.squeeze(0) if tensor.shape[0] == 1 else tensor[0]
        
        image_np = tensor.squeeze().mul(255).clamp(0, 255).byte().numpy()
        return Image.fromarray(image_np, mode='RGB')

    def create_placeholder_image(self, width=512, height=512):
        """Create a placeholder image when generation fails"""
        img = Image.new('RGB', (width, height), color=(100, 100, 100))
        try:
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            draw.text((width//2-50, height//2), "Generation\nFailed", fill=(255, 255, 255))
        except:
            pass
        
        image_array = np.array(img).astype(np.float32) / 255.0
        return torch.from_numpy(image_array).unsqueeze(0)

    def call_ssy_api(self, data, endpoint="generations"):
        """调用SSY Cloud API
        
        Args:
            data: 请求数据
            endpoint: API端点，"generations" 或 "edits"
        """
        try:
            url = f"https://router.shengsuanyun.com/api/v1/images/{endpoint}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            operation_log = f"调用API: {data.get('model', 'unknown')}\n"
            operation_log += f"端点: {url}\n"
            operation_log += f"请求参数: {list(data.keys())}\n"
            
            # 打印完整请求体（隐藏图片数据）
            debug_data = data.copy()
            if 'image' in debug_data and isinstance(debug_data['image'], str) and len(debug_data['image']) > 100:
                debug_data['image'] = f"<base64 data {len(debug_data['image'])} chars>"
            if 'images' in debug_data:
                debug_data['images'] = f"<{len(debug_data['images'])} images>"
            operation_log += f"请求体: {json.dumps(debug_data, ensure_ascii=False, indent=2)}\n"
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data, timeout=120)
            
            # 记录响应状态
            operation_log += f"响应状态码: {response.status_code}\n"
            
            # 尝试解析JSON
            try:
                result = response.json()
                operation_log += f"响应键: {list(result.keys())}\n"
            except:
                operation_log += f"响应文本: {response.text[:500]}\n"
                response.raise_for_status()
                return [], operation_log
            
            # 检查是否有错误信息
            if "error" in result:
                operation_log += f"API错误: {result['error']}\n"
                return [], operation_log
            
            all_images = []
            
            # 格式1: Google Gemini格式 (candidates)
            if "candidates" in result:
                operation_log += "使用Gemini响应格式\n"
                for candidate in result["candidates"]:
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part and "data" in part["inlineData"]:
                                try:
                                    img_data = base64.b64decode(part["inlineData"]["data"])
                                    img = Image.open(BytesIO(img_data))
                                    if img.mode != "RGB":
                                        img = img.convert("RGB")
                                    img_np = np.array(img).astype(np.float32) / 255.0
                                    img_tensor = torch.from_numpy(img_np)[None,]
                                    all_images.append(img_tensor)
                                except Exception as e:
                                    operation_log += f"解析Gemini图像失败: {str(e)}\n"
            
            # 格式2: OpenAI/Doubao格式 (data数组)
            elif "data" in result and isinstance(result["data"], list):
                operation_log += "使用OpenAI/Doubao响应格式\n"
                for item in result["data"]:
                    try:
                        # b64_json格式
                        if "b64_json" in item:
                            img_data = base64.b64decode(item["b64_json"])
                            img = Image.open(BytesIO(img_data))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                        # URL格式
                        elif "url" in item:
                            img_response = requests.get(item["url"], timeout=30)
                            img = Image.open(BytesIO(img_response.content))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                    except Exception as e:
                        operation_log += f"解析data数组图像失败: {str(e)}\n"
            
            # 格式3: 火山引擎格式 (特殊结构)
            elif "data" in result and isinstance(result["data"], dict):
                operation_log += "使用火山引擎响应格式\n"
                try:
                    data_obj = result["data"]
                    # 尝试从binary_data_base64获取
                    if "binary_data_base64" in data_obj and data_obj["binary_data_base64"]:
                        for b64_str in data_obj["binary_data_base64"]:
                            img_data = base64.b64decode(b64_str)
                            img = Image.open(BytesIO(img_data))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                    # 尝试从image_urls获取
                    elif "image_urls" in data_obj and data_obj["image_urls"]:
                        for url in data_obj["image_urls"]:
                            img_response = requests.get(url, timeout=30)
                            img = Image.open(BytesIO(img_response.content))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                except Exception as e:
                    operation_log += f"解析火山引擎格式失败: {str(e)}\n"
            
            # 格式4: 直接image字段
            elif "image" in result:
                operation_log += "使用image字段响应格式\n"
                try:
                    if isinstance(result["image"], str):
                        img_data = base64.b64decode(result["image"])
                        img = Image.open(BytesIO(img_data))
                        if img.mode != "RGB":
                            img = img.convert("RGB")
                        img_np = np.array(img).astype(np.float32) / 255.0
                        img_tensor = torch.from_numpy(img_np)[None,]
                        all_images.append(img_tensor)
                except Exception as e:
                    operation_log += f"解析image字段失败: {str(e)}\n"
            
            # 格式5: results数组 (某些API可能使用)
            elif "results" in result and isinstance(result["results"], list):
                operation_log += "使用results数组响应格式\n"
                for item in result["results"]:
                    try:
                        if "image" in item:
                            img_data = base64.b64decode(item["image"])
                            img = Image.open(BytesIO(img_data))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                        elif "url" in item:
                            img_response = requests.get(item["url"], timeout=30)
                            img = Image.open(BytesIO(img_response.content))
                            if img.mode != "RGB":
                                img = img.convert("RGB")
                            img_np = np.array(img).astype(np.float32) / 255.0
                            img_tensor = torch.from_numpy(img_np)[None,]
                            all_images.append(img_tensor)
                    except Exception as e:
                        operation_log += f"解析results图像失败: {str(e)}\n"
            
            if all_images:
                operation_log += f"✓ 成功解析 {len(all_images)} 张图像\n"
            else:
                operation_log += "✗ 未能从响应中解析出图像\n"
                operation_log += f"完整响应结构: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}\n"
            
            return all_images, operation_log
            
        except requests.exceptions.RequestException as e:
            operation_log = f"网络请求错误: {str(e)}\n"
            return [], operation_log
        except Exception as e:
            operation_log = f"API调用错误: {str(e)}\n"
            import traceback
            operation_log += f"错误详情: {traceback.format_exc()}\n"
            return [], operation_log


class SSYGoogleGenerator(SSYAPIBase):
    """Google Gemini系列图像生成器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["google/gemini-2.5-flash-image-preview", "google/gemini-3-pro-image-preview"], {
                    "default": "google/gemini-2.5-flash-image-preview"
                }),
                "prompt": ("STRING", {
                    "default": "Generate a high-quality, photorealistic image", 
                    "multiline": True
                }),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "第1张参考图片"}),
                "input_image1": ("IMAGE", {"tooltip": "第2张参考图片"}),
                "input_image2": ("IMAGE", {"tooltip": "第3张参考图片"}),
                "input_image3": ("IMAGE", {"tooltip": "第4张参考图片"}),
                "input_image4": ("IMAGE", {"tooltip": "第5张参考图片"}),
                "input_image5": ("IMAGE", {"tooltip": "第6张参考图片"}),
                "input_image6": ("IMAGE", {"tooltip": "第7张参考图片"}),
                "input_image7": ("IMAGE", {"tooltip": "第8张参考图片"}),
                "input_image8": ("IMAGE", {"tooltip": "第9张参考图片"}),
                "input_image9": ("IMAGE", {"tooltip": "第10张参考图片"}),
                "input_image10": ("IMAGE", {"tooltip": "第11张参考图片"}),
                "input_image11": ("IMAGE", {"tooltip": "第12张参考图片"}),
                "api_key": ("STRING", {
                    "default": "",
                    "password": True
                }),
                "aspect_ratio": (["1:1", "16:9", "21:9", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16"], {
                    "default": "1:1"
                }),
                "size": (["1K", "2K", "4K"], {
                    "default": "1K",
                    "tooltip": "仅gemini-3-pro-image-preview支持"
                }),
                "response_modalities": (["IMAGE", "TEXT_IMAGE"], {
                    "default": "IMAGE"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "log")
    FUNCTION = "generate"
    CATEGORY = "SSY Cloud同步任务/Google"

    def generate(self, model, prompt, input_image=None, input_image1=None, input_image2=None, 
                input_image3=None, input_image4=None, input_image5=None, input_image6=None,
                input_image7=None, input_image8=None, input_image9=None, input_image10=None,
                input_image11=None, api_key="", aspect_ratio="1:1", size="1K", 
                response_modalities="IMAGE"):
        if api_key.strip():
            self.api_key = api_key
            save_config({"SSY_API_KEY": self.api_key})

        if not self.api_key:
            return (self.create_placeholder_image(), "错误: 未提供API密钥")

        try:
            data = {
                "model": model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio
            }
            
            # 处理多张图像（最多12张）
            all_input_images = [input_image, input_image1, input_image2, input_image3, input_image4,
                              input_image5, input_image6, input_image7, input_image8, input_image9,
                              input_image10, input_image11]
            
            images_data = []
            for img in all_input_images:
                if img is not None:
                    if isinstance(img, torch.Tensor):
                        pil_image = self.tensor_to_image(img[0] if len(img.shape) == 4 else img)
                        img_byte_arr = BytesIO()
                        pil_image.save(img_byte_arr, format='PNG')
                        b64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                        images_data.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": b64_string
                            }
                        })
            
            if images_data:
                data["images"] = images_data
            
            # gemini-3-pro独有参数
            if "gemini-3-pro" in model:
                data["size"] = size
            
            # response_modalities
            if response_modalities == "IMAGE":
                data["response_modalities"] = ["IMAGE"]
            else:
                data["response_modalities"] = ["TEXT", "IMAGE"]
            
            # 豆包系列使用generations端点
            images, log = self.call_ssy_api(data, endpoint="generations")
            
            if images:
                return (torch.cat(images, dim=0), log)
            else:
                return (self.create_placeholder_image(), log)
                
        except Exception as e:
            return (self.create_placeholder_image(), f"错误: {str(e)}")


class SSYDoubaoGenerator(SSYAPIBase):
    """ByteDance Doubao系列图像生成器 - 简化版"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ([
                    "bytedance/doubao-seedream-4.5",
                    "bytedance/doubao-seedream-4.0",
                    "bytedance/doubao-seedream-3.0-t2i",
                    "bytedance/doubao-seededit-3-0-i2i"
                ], {
                    "default": "bytedance/doubao-seedream-4.5"
                }),
                "prompt": ("STRING", {
                    "default": "Generate a high-quality image", 
                    "multiline": True
                }),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "第1张参考图片"}),
                "input_image1": ("IMAGE", {"tooltip": "第2张参考图片"}),
                "input_image2": ("IMAGE", {"tooltip": "第3张参考图片"}),
                "input_image3": ("IMAGE", {"tooltip": "第4张参考图片"}),
                "input_image4": ("IMAGE", {"tooltip": "第5张参考图片"}),
                "input_image5": ("IMAGE", {"tooltip": "第6张参考图片"}),
                "input_image6": ("IMAGE", {"tooltip": "第7张参考图片"}),
                "input_image7": ("IMAGE", {"tooltip": "第8张参考图片"}),
                "input_image8": ("IMAGE", {"tooltip": "第9张参考图片"}),
                "input_image9": ("IMAGE", {"tooltip": "第10张参考图片"}),
                "api_key": ("STRING", {
                    "default": "",
                    "password": True
                }),
                "size": (["1024x1024", "1536x1024", "1024x1536", "2048x2048"], {
                    "default": "1024x1024"
                }),
                "watermark": ("BOOLEAN", {
                    "default": False
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "log")
    FUNCTION = "generate"
    CATEGORY = "SSY Cloud同步任务/Doubao"

    def generate(self, model, prompt, input_image=None, input_image1=None, input_image2=None,
                input_image3=None, input_image4=None, input_image5=None, input_image6=None,
                input_image7=None, input_image8=None, input_image9=None, api_key="", 
                size="1024x1024", watermark=False):
        if api_key.strip():
            self.api_key = api_key
            save_config({"SSY_API_KEY": self.api_key})

        if not self.api_key:
            return (self.create_placeholder_image(), "错误: 未提供API密钥")

        try:
            # 构建最简请求体
            data = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "watermark": watermark
            }
            
            # 处理多张图像（最多10张）
            all_input_images = [input_image, input_image1, input_image2, input_image3, input_image4,
                              input_image5, input_image6, input_image7, input_image8, input_image9]
            
            images_data = []
            for img in all_input_images:
                if img is not None:
                    if isinstance(img, torch.Tensor):
                        pil_image = self.tensor_to_image(img[0] if len(img.shape) == 4 else img)
                        img_byte_arr = BytesIO()
                        pil_image.save(img_byte_arr, format='PNG')
                        b64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                        # 使用data URI格式（根据API文档要求）
                        images_data.append(f"data:image/png;base64,{b64_string}")
            
            if images_data:
                # 4.0和4.5支持多图数组
                if "4.0" in model or "4.5" in model:
                    data["image"] = images_data
                else:
                    # 3.0系列只支持单图字符串
                    data["image"] = images_data[0]
            
            # 豆包系列使用generations端点
            images, log = self.call_ssy_api(data, endpoint="generations")
            
            if images:
                return (torch.cat(images, dim=0), log)
            else:
                return (self.create_placeholder_image(), log)
                
        except Exception as e:
            return (self.create_placeholder_image(), f"错误: {str(e)}")


class SSYOpenAIGenerator(SSYAPIBase):
    """OpenAI系列图像生成器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["openai/gpt-image-1"], {
                    "default": "openai/gpt-image-1"
                }),
                "prompt": ("STRING", {
                    "default": "Generate a high-quality image", 
                    "multiline": True
                }),
            },
            "optional": {
                "input_image": ("IMAGE", {"tooltip": "参考图片"}),
                "api_key": ("STRING", {
                    "default": "",
                    "password": True
                }),
                "size": (["auto", "1024x1024", "1536x1024", "1024x1536", "1792x1024", "1024x1792"], {
                    "default": "auto"
                }),
                "n": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 10
                }),
                "quality": (["auto", "high", "medium", "low", "hd", "standard"], {
                    "default": "auto"
                }),
                "background": (["auto", "transparent", "opaque"], {
                    "default": "auto",
                    "tooltip": "transparent时需使用png或webp格式"
                }),
                "output_format": (["png", "jpeg", "webp"], {
                    "default": "png"
                }),
                "output_compression": ("INT", {
                    "default": 100,
                    "min": 0,
                    "max": 100,
                    "tooltip": "webp或jpeg格式支持"
                }),
                "moderation": (["auto", "low"], {
                    "default": "auto"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "log")
    FUNCTION = "generate"
    CATEGORY = "SSY Cloud同步任务/OpenAI"

    def generate(self, model, prompt, input_image=None, api_key="", size="auto", n=1, quality="auto",
                background="auto", output_format="png", output_compression=100, moderation="auto"):
        if api_key.strip():
            self.api_key = api_key
            save_config({"SSY_API_KEY": self.api_key})

        if not self.api_key:
            return (self.create_placeholder_image(), "错误: 未提供API密钥")

        try:
            # 按照API文档构建请求体，两个端点参数完全相同
            data = {
                "model": model,
                "prompt": prompt
            }
            
            # 处理输入图像
            has_image = False
            if input_image is not None:
                if isinstance(input_image, torch.Tensor):
                    pil_image = self.tensor_to_image(input_image[0] if len(input_image.shape) == 4 else input_image)
                    img_byte_arr = BytesIO()
                    pil_image.save(img_byte_arr, format='PNG')
                    b64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                    data["image"] = f"data:image/png;base64,{b64_string}"
                    has_image = True
            
            # 添加其他参数（文生图和图生图都支持）
            if n != 1:
                data["n"] = n
            if size != "auto":
                data["size"] = size
            if quality != "auto":
                data["quality"] = quality
            if output_format != "png":
                data["output_format"] = output_format
            if background != "auto":
                data["background"] = background
            if moderation != "auto":
                data["moderation"] = moderation
            if output_compression != 100:
                data["output_compression"] = output_compression
            
            # 根据是否有图片选择端点：有图用edits，无图用generations
            endpoint = "edits" if has_image else "generations"
            images, log = self.call_ssy_api(data, endpoint=endpoint)
            
            if images:
                return (torch.cat(images, dim=0), log)
            else:
                return (self.create_placeholder_image(), log)
                
        except Exception as e:
            return (self.create_placeholder_image(), f"错误: {str(e)}")


class SSYBytedanceProcessor(SSYAPIBase):
    """火山引擎图像处理器（增强/放大）"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": (["bytedance/image_enhance", "bytedance/image_upscale"], {
                    "default": "bytedance/image_enhance"
                }),
                "input_image": ("IMAGE", {}),
            },
            "optional": {
                "api_key": ("STRING", {
                    "default": "",
                    "password": True
                }),
                "model_quality": (["HQ", "MQ", "LQ"], {
                    "default": "MQ",
                    "tooltip": "upscale模型必选：HQ适用高质量图，MQ中等，LQ适用低质量图"
                }),
                "resolution_boundary": (["144p", "240p", "360p", "480p", "540p", "720p", "1080p", "2k"], {
                    "default": "1080p"
                }),
                "jpg_quality": ("INT", {
                    "default": 95,
                    "min": 0,
                    "max": 100
                }),
                "result_format": ([0, 1], {
                    "default": 0,
                    "tooltip": "0=png格式, 1=jpeg格式"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "log")
    FUNCTION = "process"
    CATEGORY = "SSY Cloud同步任务/Bytedance"

    def process(self, model, input_image, api_key="", model_quality="MQ", 
               resolution_boundary="1080p", jpg_quality=95, result_format=0):
        if api_key.strip():
            self.api_key = api_key
            save_config({"SSY_API_KEY": self.api_key})

        if not self.api_key:
            return (self.create_placeholder_image(), "错误: 未提供API密钥")

        try:
            # 处理图像
            if isinstance(input_image, torch.Tensor):
                pil_image = self.tensor_to_image(input_image[0] if len(input_image.shape) == 4 else input_image)
                img_byte_arr = BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                b64_string = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
            
            data = {
                "model": model,
                "binary_data_base64": [b64_string],
                "resolution_boundary": resolution_boundary,
                "jpg_quality": jpg_quality,
                "result_format": result_format,
                "return_url": True
            }
            
            # upscale模型必须的参数
            if "upscale" in model:
                data["model_quality"] = model_quality
            
            # 火山引擎使用edits端点
            images, log = self.call_ssy_api(data, endpoint="edits")
            
            if images:
                return (torch.cat(images, dim=0), log)
            else:
                return (self.create_placeholder_image(), log)
                
        except Exception as e:
            return (self.create_placeholder_image(), f"错误: {str(e)}")


# Node registration
NODE_CLASS_MAPPINGS = {
    "SSYGoogleGenerator": SSYGoogleGenerator,
    "SSYDoubaoGenerator": SSYDoubaoGenerator,
    "SSYOpenAIGenerator": SSYOpenAIGenerator,
    "SSYBytedanceProcessor": SSYBytedanceProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SSYGoogleGenerator": "SSY Google Generator（同步任务）🌟",
    "SSYDoubaoGenerator": "SSY Doubao Generator（同步任务）🎨",
    "SSYOpenAIGenerator": "SSY OpenAI Generator（同步任务）🤖",
    "SSYBytedanceProcessor": "SSY Bytedance Processor（同步任务）🔧",
}
