# story_demo.py
import pygame

# ---------- 기본 설정 ----------
SCREEN_W, SCREEN_H = 960, 540
FONT_NAME = "malgungothic"  # 윈도우: 맑은 고딕. 없으면 시스템 폰트로 대체됨.
BG_CLEAR_COLOR = (17, 19, 24)

# ---------- 스토리 데이터 ----------
STORY_DATA = {
    "엘테리아 (수도섬)": (
        "세금집행관 리세온\n"
        "수도 엘테리아는 제국의 심장이다. 모든 돈의 흐름이 이곳에서 시작되고, 이곳에서 사라진다. "
        "리세온은 세금을 피처럼 여기는 남자다. 하지만 그 피가 누구의 몸을 돌고 있는지는 아무도 말하지 않는다.\n\n"
        "공물문 뒤편의 기록고에는 제국의 숨겨진 장부가 있다. "
        "수많은 이름과 숫자, 그리고 사라진 사람들의 흔적. "
        "리세온은 자신이 믿어온 질서가 과연 정의였는지를 처음으로 의심하기 시작했다."
    ),
    "칼단 (반란군 본거지)": (
        "개혁군 지휘관 세라\n"
        "칼단은 제국의 밑바닥이자 반란의 심장이다. "
        "광산의 불빛은 낮에도 꺼지지 않는다. 노동자들은 자신이 캔 흑철의 값조차 모른 채 죽어간다.\n\n"
        "세라는 그들의 피와 땀으로 반란의 기금을 모은다. "
        "그녀에게 돈은 단순한 수단이 아니라, 잃어버린 존엄을 되찾기 위한 불씨다. "
        "칼단의 노래는 점점 더 많은 이들의 가슴 속에서 번져간다."
    ),
    "세이렌 (무역/밀수섬)": (
        "항로상 마이로\n"
        "세이렌은 바람보다 빠른 섬이다. 거래와 정보가 뒤섞여 하루에도 수천 번의 돈의 흐름이 바뀐다. "
        "마이로는 그 흐름을 읽는 자다. 그는 신도 왕도 믿지 않는다. 오직 숫자만이 그에게 진실을 말한다.\n\n"
        "밤마다 검은 항로 위로 은빛 등불이 떠오른다. "
        "그것은 반란군의 물자일 수도, 정부의 금괴일 수도 있다. "
        "마이로에게 중요한 건 단 하나 — 누가 먼저 값을 치르느냐다."
    ),
    "노바라 (신전섬)": (
        "청지기 라나\n"
        "노바라의 신전은 하늘에서 가장 화려한 금으로 장식되어 있다. "
        "신의 뜻은 기도보다 헌금의 액수로 정해진다. "
        "라나는 신을 사랑했지만, 그 신이 이익을 계산하는 모습을 보고 침묵했다.\n\n"
        "그녀는 이제 말없이 신전의 문을 닫는다. "
        "그리고 마지막 헌금 바구니에 쪽지를 남긴다. "
        "‘신은 사람의 마음에 머물 때만 빛난다.’"
    ),
    "아르테론 (연구섬)": (
        "학사 오른\n"
        "아르테론은 지식과 기술의 섬이지만, 이곳의 연구는 언제나 자금이 방향을 정한다. "
        "새로운 발명은 투자자 없이는 빛을 볼 수 없고, 기술은 돈이 닿는 곳에서만 자란다.\n\n"
        "오른은 자신이 만든 감시기를 바라보며 생각한다. "
        "이 장치가 사람을 보호할 수도, 지배할 수도 있다는 것을. "
        "그는 손끝의 도면 위에, ‘이익 없는 혁신은 존재할 수 있을까?’라고 적는다."
    ),
    "바르노스 (황폐섬)": (
        "폐허의 정령 바른\n"
        "한때 바르노스에는 황금 들판이 있었다. 그러나 이제 그 자리는 잿빛 바람만 돈다. "
        "불탄 마을의 잔해 속에도 금화 몇 닢이 반짝이고 있었다.\n\n"
        "바른은 그것을 집어든 인간을 가만히 바라본다. "
        "누군가는 그것으로 생존을, 누군가는 그것으로 전쟁을 산다. "
        "정령은 오래된 목소리로 속삭인다. "
        "‘돈이 흐르는 한, 불도 꺼지지 않겠지.’"
    ),
}



# ---------- 유틸 ----------
def wrap_text(text, font, max_width):
    lines = []
    for raw_line in text.split("\n"):
        if raw_line.strip() == "":
            lines.append("")
            continue
        words = raw_line.split(" ")
        cur = ""
        for w in words:
            test = w if cur == "" else cur + " " + w
            if font.size(test)[0] <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
    return lines

class Button:
    def __init__(self, rect: pygame.Rect, label: str, font: pygame.font.Font):
        self.rect = rect
        self.label = label
        self.font = font

    def draw(self, surf, hovered: bool, selected: bool):
        base = (36, 42, 52)
        hover = (50, 62, 78)
        sel = (70, 96, 132)
        border = (70, 80, 95)
        color = sel if selected else (hover if hovered else base)
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        pygame.draw.rect(surf, border, self.rect, 1, border_radius=8)
        img = self.font.render(self.label, True, (240, 240, 245))
        surf.blit(img, img.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

class StoryView:
    def __init__(self):
        self.sidebar_w = 260
        self.margin = 14
        self.content_w = SCREEN_W - self.sidebar_w - self.margin * 3
        self.content_h = SCREEN_H - self.margin * 2
        self.active = True
        self.selected_key = list(STORY_DATA.keys())[0]
        self.scroll = 0

        # 폰트
        try:
            self.title_font = pygame.font.SysFont(FONT_NAME, 24)
            self.item_font = pygame.font.SysFont(FONT_NAME, 18)
            self.body_font = pygame.font.SysFont(FONT_NAME, 18)
        except:
            self.title_font = pygame.font.SysFont(None, 24)
            self.item_font = pygame.font.SysFont(None, 18)
            self.body_font = pygame.font.SysFont(None, 18)

        # 버튼 생성
        self.buttons = []
        y = self.margin + 42
        for key in STORY_DATA.keys():
            rect = pygame.Rect(self.margin, y, self.sidebar_w - self.margin * 2, 42)
            self.buttons.append(Button(rect, key, self.item_font))
            y += 48

        # 본문 캐시
        self._cached_lines = None
        self._cached_key = None
        self._line_height = self.body_font.get_linesize()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.active = False
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.scroll += 24
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.scroll -= 24
            elif event.key == pygame.K_PAGEUP:
                self.scroll -= 240
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll += 240

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for b in self.buttons:
                    if b.hit(event.pos):
                        self.selected_key = b.label
                        self.scroll = 0
                        self._cached_key = None
                        break
            elif event.button == 4:  # wheel up
                self.scroll -= 36
            elif event.button == 5:  # wheel down
                self.scroll += 36

    def draw(self, surf):
        # 배경
        surf.fill(BG_CLEAR_COLOR)

        # 사이드바 패널
        sidebar_rect = pygame.Rect(self.margin, self.margin,
                                   self.sidebar_w - self.margin, SCREEN_H - self.margin * 2)
        pygame.draw.rect(surf, (22, 26, 32), sidebar_rect, border_radius=12)
        pygame.draw.rect(surf, (60, 70, 85), sidebar_rect, 1, border_radius=12)

        # 컨텐츠 패널
        content_rect = pygame.Rect(self.sidebar_w + self.margin * 2, self.margin,
                                   self.content_w, self.content_h)
        pygame.draw.rect(surf, (18, 20, 24), content_rect, border_radius=12)
        pygame.draw.rect(surf, (60, 70, 85), content_rect, 1, border_radius=12)

        # 제목
        title_img = self.title_font.render("하늘섬 스토리", True, (250, 230, 170))
        surf.blit(title_img, (self.margin + 8, self.margin + 6))

        # 버튼
        mouse = pygame.mouse.get_pos()
        for b in self.buttons:
            hovered = b.hit(mouse)
            selected = (b.label == self.selected_key)
            b.draw(surf, hovered, selected)

        # 본문 래핑/캐시
        if self._cached_key != self.selected_key:
            text = STORY_DATA[self.selected_key]
            lines = wrap_text(text, self.body_font, self.content_w - 24)
            self._cached_lines = lines
            self._cached_key = self.selected_key
            self.scroll = 0

        # 스크롤 한계
        total_h = len(self._cached_lines) * self._line_height if self._cached_lines else 0
        max_scroll = max(0, total_h - (self.content_h - 24))
        self.scroll = max(0, min(self.scroll, max_scroll))

        # 본문 그리기
        if self._cached_lines:
            x = content_rect.x + 12
            y_start = content_rect.y + 12 - self.scroll
            for i, line in enumerate(self._cached_lines):
                img = self.body_font.render(line, True, (235, 235, 240))
                surf.blit(img, (x, y_start + i * self._line_height))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("하늘섬 스토리 뷰어")
    clock = pygame.time.Clock()

    view = StoryView()

    running = True
    while running and view.active:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            view.handle_event(event)

        view.draw(screen)
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
