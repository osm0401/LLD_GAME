# util/fonts.py
# -----------------------------------------
# 모든 텍스트를 JUA.ttf로 로드하는 헬퍼
# -----------------------------------------
import pygame
import os

def load_font_jua(size: int) -> pygame.font.Font:
    """
    assets/JUA.ttf 를 강제로 사용한다.
    파일이 없으면 친절한 에러를 던져서 바로 원인 확인 가능.
    """
    project_root = os.path.dirname(os.path.dirname(__file__))  # util/.. = 프로젝트 루트
    font_path = os.path.join(project_root, "assets", "JUA.ttf")
    if not os.path.exists(font_path):
        raise FileNotFoundError(
            f"JUA.ttf not found at: {font_path}\n"
            f"→ 'assets' 폴더에 JUA.ttf를 넣어 주세요."
        )
    return pygame.font.Font(font_path, size)
