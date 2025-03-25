"""
安卓设备自动化模块

该模块提供安卓设备的UI自动化操作功能，主要用于：
- 自动发布内容
- 屏幕解锁
- 应用操作
"""

import logging
import os
import time
import uiautomator2 as u2
from core.config import Settings

logger = logging.getLogger(__name__)

class AndroidAutomation:
    def __init__(self, device_name: str):
        """
        初始化自动化实例
        
        Args:
            device_name: 设备名称（不是设备ID）
        """
        self.device_name = device_name
        self.device_id = Settings.DEVICE_MAPPING[device_name]
        self.d = None
        
        # 从设备配置中获取详细设置
        device_config = Settings.DEVICE_CONFIG[device_name]
        self.app_package = device_config.get('app_package', Settings.AUTOMATION_CONFIG['APP_PACKAGE'])
        self.lock_password = device_config['lock_password']
        self.wait_timeout = device_config.get('wait_timeout', Settings.AUTOMATION_CONFIG['WAIT_TIMEOUT'])
        
        logger.info(f"初始化设备: {device_name} (ID: {self.device_id})")
        logger.debug(f"使用配置 - 应用包名: {self.app_package}, 等待超时: {self.wait_timeout}秒")

    def connect_device(self):
        """连接设备"""
        try:
            self.d = u2.connect(self.device_id)
            logger.info(f"成功连接设备: {self.device_id}")
            return True
        except Exception as e:
            logger.error(f"设备连接失败: {str(e)}")
            return False

    def post_content(self, title, content, image_paths):
        """
        发布内容
        
        Args:
            title: 发布内容的标题
            content: 发布内容的正文
            image_paths: 图片路径列表
            
        Returns:
            tuple: (是否成功, 状态消息)
        """
        try:
            logger.info("开始发布内容")
            logger.debug(f"标题: {title if title else '[无标题]'}")
            logger.debug(f"正文长度: {len(content) if content else 0}")
            logger.debug(f"图片数量: {len(image_paths)}")

            # 获取时间文件夹名
            logger.debug(f"原始路径: {image_paths[0]}")
            path_parts = image_paths[0].split(os.path.sep)
            logger.debug(f"path_parts: {path_parts}")
            
            # 找到 'img' 目录的索引，它的上一级就是时间文件夹
            img_index = path_parts.index('imgs')
            time_str = path_parts[img_index - 1]
            logger.debug(f"解析到的时间文件夹: {time_str}")

            # 解锁屏幕
            self.d.screen_on()
            self.d.swipe(500, 2500, 500, 500, duration=1.0)
            
            # 添加等待和重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # 等待密码输入界面
                    if self.d(resourceId="com.android.systemui:id/digit_text", text="0").exists(timeout=5):
                        for digit in self.lock_password:
                            self.d(resourceId="com.android.systemui:id/digit_text", text=str(digit)).click()
                        break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"密码输入失败: {str(e)}")
                    time.sleep(1)

            # 启动应用
            self.d.app_start(self.app_package)
            self.d.wait_activity(self.app_package, timeout=self.wait_timeout)
            logger.debug("应用启动成功")

            # 点击发布按钮
            self.d.xpath('//*[@content-desc="发布"]/android.widget.ImageView[1]').click()
            logger.debug("点击发布按钮")

            # 尝试多种方式点击"全部"按钮
            try:
                # 方式1：使用原有的xpath
                all_photos = self.d.xpath('//*[@resource-id="android:id/content"]/android.widget.FrameLayout[1]/android.widget.FrameLayout[3]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.RelativeLayout[1]/android.widget.LinearLayout[1]')
                if all_photos.exists:
                    all_photos.click()
                else:
                    # 方式2：尝试使用文本定位
                    self.d(text="全部").click()
            except Exception as e:
                logger.error(f"点击'全部'按钮失败: {str(e)}")
                return False, "SELECT_ALBUM_FAILED"
            
            logger.debug("点击'全部'按钮成功")

            # 等待文件夹列表加载
            time.sleep(1)

            # 选择时间文件夹
            logger.debug(f"准备选择文件夹: {time_str}")

            # 添加重试机制选择文件夹
            for attempt in range(max_retries):
                try:
                    target_element = self.d(resourceId=f"{self.app_package}:id/-", text=time_str)
                    if target_element.exists(timeout=5):
                        target_element.click()
                        logger.debug(f"成功选择文件夹: {time_str}")
                        break
                    else:
                        # 如果找不到，尝试滚动列表
                        self.d.swipe(500, 1000, 500, 200)
                        time.sleep(0.5)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"选择文件夹失败: {str(e)}")
                        return False, "FOLDER_NOT_FOUND"
                    time.sleep(1)

            self.d.wait_activity('', timeout=self.wait_timeout)

            # 选择图片
            base_xpath = '//androidx.viewpager.widget.ViewPager/androidx.recyclerview.widget.RecyclerView[1]/android.widget.FrameLayout[1]/androidx.recyclerview.widget.RecyclerView[1]/android.widget.FrameLayout[{}]/android.widget.FrameLayout[1]/android.widget.RelativeLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.ImageView[1]'
            
            index = 1
            while True:
                xpath = base_xpath.format(index)
                if self.d.xpath(xpath).exists:
                    logger.debug(f"选择第 {index} 张图片")
                    self.d.xpath(xpath).click()
                    index += 1
                else:
                    logger.info(f"共选择 {index - 1} 张图片")
                    break

            if index - 1 == 0:
                logger.error("未能选择任何图片")
                return False, "NO_IMAGES_SELECTED"

            self.d.click(0.741, 0.964)  # 点击确认按钮

            # 点击下一步
            next_button = self.d(resourceId=f"{self.app_package}:id/-", text="下一步")
            if not next_button.exists(timeout=5):
                logger.error("找不到下一步按钮")
                return False, "NEXT_BUTTON_NOT_FOUND"

            next_button.click()
            logger.debug("点击下一步")

            # 根据是否有标题和正文来决定操作流程
            if title or content:
                logger.debug("检测到标题或正文内容，进行输入操作")
                # 输入标题（如果有）
                if title:
                    self.d(resourceId=f"{self.app_package}:id/-", text="添加标题").click()
                    self.d.send_keys(title)
                    logger.debug(f"输入标题: {title}")

                # 输入正文（如果有）
                if content:
                    self.d.xpath(
                        '//android.widget.ScrollView/android.widget.LinearLayout[1]/android.widget.FrameLayout[3]/android.widget.LinearLayout[1]/android.view.ViewGroup[1]/android.widget.LinearLayout[1]').click()
                    self.d.send_keys(content)
                    logger.debug("输入正文完成")

                # 点击发布按钮
                self.d(resourceId=f"{self.app_package}:id/-", text="发布").click()
            else:
                logger.debug("无标题和正文内容，直接发布")
                # 直接点击发布笔记按钮
                self.d(resourceId=f"{self.app_package}:id/-", text="发布笔记").click()

            logger.info("发布操作完成")
            return True, "SUCCESS"

        except Exception as e:
            logger.error(f"发布内容失败: {str(e)}")
            return False, "AUTOMATION_FAILED" 