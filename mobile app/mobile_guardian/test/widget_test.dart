// Basic smoke test for Omega Mobile Guardian app
import 'package:flutter_test/flutter_test.dart';
import 'package:mobile_guardian/main.dart';

void main() {
  testWidgets('App starts and renders SplashScreen', (WidgetTester tester) async {
    await tester.pumpWidget(const MobileGuardianApp());
    // SplashScreen should be visible on startup
    expect(find.text('OMEGA GUARDIAN'), findsOneWidget);
  });
}
