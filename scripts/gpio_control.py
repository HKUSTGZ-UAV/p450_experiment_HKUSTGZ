import os
import time


class GPIOCtrl:
    def __init__(self, gpio_name="PAC.06"):
        self.gpio_name = gpio_name
        self.gpio_path = f"/sys/class/gpio/{gpio_name}"
        self.value_path = f"{self.gpio_path}/value"
        
        # 检查GPIO是否已导出
        if not os.path.exists(self.gpio_path):
            raise FileNotFoundError(f"GPIO {gpio_name} 未导出，请先执行导出操作")
            
        # 检查value文件是否存在且可写
        if not os.access(self.value_path, os.W_OK):
            raise PermissionError(f"没有写入权限，请确保 {self.value_path} 可写")

    def open(self):
        with open(self.value_path, 'w') as f:
            f.write('1')
        print(f"GPIO {self.gpio_name} 已打开（高电平）")

    def close(self):
        with open(self.value_path, 'w') as f:
            f.write('0')
        print(f"GPIO {self.gpio_name} 已关闭（低电平）")

# 使用示例
if __name__ == "__main__":
    try:
        # 创建GPIO控制器实例
        gpio = GPIOCtrl("PAC.06")
        time.sleep(5)
        # 打开GPIO
        gpio.open()
        
        # 模拟工作一段时间
        time.sleep(2)
        
        # 关闭GPIO
        gpio.close()
        
    except Exception as e:
        print(f"操作失败: {e}")