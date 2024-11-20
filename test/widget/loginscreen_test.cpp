#include "src/widget/loginscreen.h"

#include <QTest>

#include "src/persistence/settings.h"
#include "src/widget/style.h"

class TestLoginScreen : public QObject
{
    Q_OBJECT
private slots:
    void testLoginScreen();
};

void TestLoginScreen::testLoginScreen()
{
    Paths paths;
    Style style;
    int themeColor = 0; // Default
    QString profileName = "test-user";
    LoginScreen loginScreen(paths, style, themeColor, profileName);

    const QPixmap actual = loginScreen.grab();
    const QPixmap expected = QPixmap(":/test/images/loginscreen.png");
    QCOMPARE(actual, expected);
}

QTEST_MAIN(TestLoginScreen)
#include "loginscreen_test.moc"
