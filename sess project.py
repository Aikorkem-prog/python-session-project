import sys
import random
from PyQt5.QtWidgets import (QMainWindow, QFrame, QDesktopWidget, QApplication,
                             QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QStackedLayout)
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor

class Shape:
    coordsTable = (
        ((0, 0),     (0, 0),     (0, 0),     (0, 0)),
        ((0, -1),    (0, 0),     (-1, 0),    (-1, 1)),
        ((0, -1),    (0, 0),     (1, 0),     (1, 1)),
        ((0, -1),    (0, 0),     (0, 1),     (0, 2)),
        ((-1, 0),    (0, 0),     (1, 0),     (0, 1)),
        ((0, 0),     (1, 0),     (0, 1),     (1, 1)),
        ((-1, -1),   (0, -1),    (0, 0),     (0, 1)),
        ((1, -1),    (0, -1),    (0, 0),     (0, 1))
    )

    def __init__(self):
        self.coords = [[0,0] for _ in range(4)]
        self.pieceShape = 0
        self.setShape(0)

    def shape(self):
        return self.pieceShape

    def setShape(self, shape):
        table = Shape.coordsTable[shape]
        for i in range(4):
            for j in range(2):
                self.coords[i][j] = table[i][j]
        self.pieceShape = shape

    def setRandomShape(self):
        self.setShape(random.randint(1, 7))

    def x(self, index):
        return self.coords[index][0]

    def y(self, index):
        return self.coords[index][1]

    def minX(self):
        return min([x[0] for x in self.coords])

    def maxX(self):
        return max([x[0] for x in self.coords])

    def minY(self):
        return min([x[1] for x in self.coords])

    def maxY(self):
        return max([x[1] for x in self.coords])

    def rotateLeft(self):
        if self.pieceShape == 5:
            return self
        result = Shape()
        result.pieceShape = self.pieceShape
        for i in range(4):
            result.coords[i][0] = self.y(i)
            result.coords[i][1] = -self.x(i)
        return result

    def rotateRight(self):
        if self.pieceShape == 5:
            return self
        result = Shape()
        result.pieceShape = self.pieceShape
        for i in range(4):
            result.coords[i][0] = -self.y(i)
            result.coords[i][1] = self.x(i)
        return result

class NextPieceWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.next_piece = None
        self.setFixedSize(100, 100)
        self.setStyleSheet("background-color: #1e1e1e;")

    def set_next_piece(self, piece):
        self.next_piece = piece
        self.update()

    def paintEvent(self, event):
        if self.next_piece is None:
            return
        painter = QPainter(self)
        color_table = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                       0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]
        color = QColor(color_table[self.next_piece.shape()])
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        for i in range(4):
            x = self.next_piece.x(i)
            y = self.next_piece.y(i)
            painter.drawRect((x + 1) * 20, (y + 1) * 20, 18, 18)

class Board(QFrame):
    BoardWidth = 10
    BoardHeight = 22
    Speed = 300

    msg2Statusbar = pyqtSignal(str)
    gameOverSignal = pyqtSignal()

    def __init__(self, parent, next_piece_widget=None):
        super().__init__(parent)
        self.next_piece_widget = next_piece_widget
        self.initBoard()

    def initBoard(self):
        self.timer = QBasicTimer()
        self.isStarted = False
        self.isPaused = False
        self.curPiece = Shape()
        self.nextPiece = Shape()
        self.curX = 0
        self.curY = 0
        self.numLinesRemoved = 0
        self.board = [0] * (Board.BoardWidth * Board.BoardHeight)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("background-color: #1e1e1e;")

    def shapeAt(self, x, y):
        return self.board[(y * Board.BoardWidth) + x]

    def setShapeAt(self, x, y, shape):
        self.board[(y * Board.BoardWidth) + x] = shape

    def squareWidth(self):
        return self.contentsRect().width() // Board.BoardWidth

    def squareHeight(self):
        return self.contentsRect().height() // Board.BoardHeight

    def start(self):
        if self.isPaused:
            return
        self.isStarted = True
        self.isWaitingAfterLine = False
        self.numLinesRemoved = 0
        self.clearBoard()
        self.msg2Statusbar.emit(str(self.numLinesRemoved))
        self.newPiece()
        self.timer.start(Board.Speed, self)

    def pause(self):
        if not self.isStarted:
            return
        self.isPaused = not self.isPaused
        if self.isPaused:
            self.timer.stop()
            self.msg2Statusbar.emit("paused")
        else:
            self.timer.start(Board.Speed, self)
            self.msg2Statusbar.emit(str(self.numLinesRemoved))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.contentsRect()
        boardTop = rect.bottom() - Board.BoardHeight * self.squareHeight()

        for i in range(Board.BoardHeight):
            for j in range(Board.BoardWidth):
                shape = self.shapeAt(j, Board.BoardHeight - i - 1)
                if shape != 0:
                    self.drawSquare(painter,
                        rect.left() + j * self.squareWidth(),
                        boardTop + i * self.squareHeight(), shape)

        if self.curPiece.shape() != 0:
            for i in range(4):
                x = self.curX + self.curPiece.x(i)
                y = self.curY - self.curPiece.y(i)
                self.drawSquare(painter, rect.left() + x * self.squareWidth(),
                                boardTop + (Board.BoardHeight - y - 1) * self.squareHeight(),
                                self.curPiece.shape())

    def drawSquare(self, painter, x, y, shape):
        colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]
        color = QColor(colorTable[shape])
        painter.fillRect(x + 1, y + 1, self.squareWidth() - 2,
                         self.squareHeight() - 2, color)

    def keyPressEvent(self, event):
        if not self.isStarted or self.curPiece.shape() == 0:
            super(Board, self).keyPressEvent(event)
            return
        key = event.key()
        if key == Qt.Key_P:
            self.pause()
            return
        if self.isPaused:
            return
        elif key == Qt.Key_Left:
            self.tryMove(self.curPiece, self.curX - 1, self.curY)
        elif key == Qt.Key_Right:
            self.tryMove(self.curPiece, self.curX + 1, self.curY)
        elif key == Qt.Key_Down:
            self.tryMove(self.curPiece.rotateRight(), self.curX, self.curY)
        elif key == Qt.Key_Up:
            self.tryMove(self.curPiece.rotateLeft(), self.curX, self.curY)
        elif key == Qt.Key_Space:
            self.dropDown()
        elif key == Qt.Key_D:
            self.oneLineDown()
        else:
            super(Board, self).keyPressEvent(event)

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.isWaitingAfterLine:
                self.isWaitingAfterLine = False
                self.newPiece()
            else:
                self.oneLineDown()
        else:
            super(Board, self).timerEvent(event)

    def clearBoard(self):
        self.board = [0] * (Board.BoardWidth * Board.BoardHeight)

    def dropDown(self):
        newY = self.curY
        while newY > 0:
            if not self.tryMove(self.curPiece, self.curX, newY - 1):
                break
            newY -= 1
        self.pieceDropped()

    def oneLineDown(self):
        if not self.tryMove(self.curPiece, self.curX, self.curY - 1):
            self.pieceDropped()

    def pieceDropped(self):
        for i in range(4):
            x = self.curX + self.curPiece.x(i)
            y = self.curY - self.curPiece.y(i)
            self.setShapeAt(x, y, self.curPiece.shape())
        self.removeFullLines()
        if not self.isWaitingAfterLine:
            self.newPiece()

    def removeFullLines(self):
        rowsToRemove = []
        for i in range(Board.BoardHeight):
            if all(self.shapeAt(j, i) != 0 for j in range(Board.BoardWidth)):
                rowsToRemove.append(i)
        rowsToRemove.reverse()
        for m in rowsToRemove:
            for k in range(m, Board.BoardHeight - 1):
                for l in range(Board.BoardWidth):
                    self.setShapeAt(l, k, self.shapeAt(l, k + 1))
        if rowsToRemove:
            self.numLinesRemoved += len(rowsToRemove)
            self.msg2Statusbar.emit(str(self.numLinesRemoved))
            self.isWaitingAfterLine = True
            self.curPiece.setShape(0)
            self.update()

    def newPiece(self):
        self.curPiece = self.nextPiece
        self.nextPiece = Shape()
        self.nextPiece.setRandomShape()
        if self.next_piece_widget:
            self.next_piece_widget.set_next_piece(self.nextPiece)
        self.curX = Board.BoardWidth // 2 + 1
        self.curY = Board.BoardHeight - 1 + self.curPiece.minY()
        if not self.tryMove(self.curPiece, self.curX, self.curY):
            self.curPiece.setShape(0)
            self.timer.stop()
            self.isStarted = False
            self.msg2Statusbar.emit("Game over")
            self.gameOverSignal.emit()

    def tryMove(self, newPiece, newX, newY):
        for i in range(4):
            x = newX + newPiece.x(i)
            y = newY - newPiece.y(i)
            if x < 0 or x >= Board.BoardWidth or y < 0 or y >= Board.BoardHeight:
                return False
            if self.shapeAt(x, y) != 0:
                return False
        self.curPiece = newPiece
        self.curX = newX
        self.curY = newY
        self.update()
        return True

class Tetris(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.stack = QStackedLayout()
        self.start_widget = QWidget()
        start_layout = QVBoxLayout()
        start_button = QPushButton("Start Game")
        start_button.clicked.connect(self.start_game)
        start_layout.addWidget(start_button)
        self.start_widget.setLayout(start_layout)

        self.game_widget = QWidget()
        game_layout = QHBoxLayout()

        self.next_piece_widget = NextPieceWidget()
        self.tboard = Board(self, self.next_piece_widget)
        self.tboard.msg2Statusbar.connect(self.update_score)
        self.tboard.gameOverSignal.connect(self.show_game_over)

        self.score_label = QLabel("Score: 0")
        self.score_label.setStyleSheet("color: white; font-size: 14px;")

        side_layout = QVBoxLayout()
        side_label = QLabel("Следующая фигура:")
        side_label.setAlignment(Qt.AlignHCenter)
        side_label.setStyleSheet("color: white; font-size: 14px;")
        side_layout.addWidget(side_label)
        side_layout.addWidget(self.next_piece_widget)
        side_layout.addWidget(self.score_label)
        side_layout.addStretch()

        game_layout.addWidget(self.tboard)
        game_layout.addLayout(side_layout)

        self.game_widget.setLayout(game_layout)

        self.game_over_widget = QWidget()
        game_over_layout = QVBoxLayout()
        self.game_over_label = QLabel("Game Over")
        self.game_over_label.setAlignment(Qt.AlignCenter)
        self.game_over_label.setStyleSheet("color: white; font-size: 20px;")
        self.restart_button = QPushButton("Restart Game")
        self.restart_button.clicked.connect(self.start_game)
        game_over_layout.addWidget(self.game_over_label)
        game_over_layout.addWidget(self.restart_button)
        self.game_over_widget.setLayout(game_over_layout)

        self.stack.addWidget(self.start_widget)
        self.stack.addWidget(self.game_widget)
        self.stack.addWidget(self.game_over_widget)

        central_widget = QWidget()
        central_widget.setLayout(self.stack)
        self.setCentralWidget(central_widget)
        self.stack.setCurrentWidget(self.start_widget)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #0fff66;
                font-size: 16px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                font-size: 16px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
        """)

        self.setWindowTitle('Tetris')
        self.resize(500, 650)
        self.center()

    def start_game(self):
        self.stack.setCurrentWidget(self.game_widget)
        self.tboard.start()

    def show_game_over(self):
        self.stack.setCurrentWidget(self.game_over_widget)

    def update_score(self, score):
        if score.isdigit():
            self.score_label.setText(f"Score: {score}")

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2,
                  (screen.height() - size.height()) // 2)

if __name__ == '__main__':
    app = QApplication([])
    tetris = Tetris()
    tetris.show()
    sys.exit(app.exec_())
