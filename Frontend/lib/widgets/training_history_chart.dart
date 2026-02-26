import 'dart:math' as math;
import 'package:flutter/material.dart';

class TrainingHistoryChart extends StatelessWidget {
  final List<Map<String, dynamic>> history;

  const TrainingHistoryChart({
    super.key,
    required this.history,
  });

  @override
  Widget build(BuildContext context) {
    if (history.isEmpty) {
      return Text(
        'No training history is available.',
        style: Theme.of(context).textTheme.titleMedium,
      );
    }

    final epochs = history
        .map((e) => (e['epoch'] as num?)?.toDouble() ?? 0.0)
        .toList(growable: false);

    final losses = history
        .map((e) => (e['train_loss'] as num?)?.toDouble() ?? 0.0)
        .toList(growable: false);

    final accs = history
        .map((e) => (e['train_acc'] as num?)?.toDouble() ?? 0.0)
        .toList(growable: false);

    final colorScheme = Theme.of(context).colorScheme;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _ChartSection(
          title: 'Training Loss',
          subtitle: 'epoch → loss',
          x: epochs,
          y: losses,
          lineColor: colorScheme.error,
        ),
        const SizedBox(height: 16),
        _ChartSection(
          title: 'Training Accuracy',
          subtitle: 'epoch → acc',
          x: epochs,
          y: accs,
          lineColor: colorScheme.primary,
          yMinOverride: 0.0,
          yMaxOverride: 1.0,
        ),
      ],
    );
  }
}

class _ChartSection extends StatelessWidget {
  final String title;
  final String subtitle;
  final List<double> x;
  final List<double> y;
  final Color lineColor;
  final double? yMinOverride;
  final double? yMaxOverride;

  const _ChartSection({
    required this.title,
    required this.subtitle,
    required this.x,
    required this.y,
    required this.lineColor,
    this.yMinOverride,
    this.yMaxOverride,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;

    // 🔥 글자 크기 키움
    final chartTextStyle =
        (textTheme.bodyMedium ?? const TextStyle()).copyWith(
      color: Colors.black,
      fontSize: 16,
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(title, style: textTheme.headlineMedium),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: textTheme.titleLarge?.copyWith(color: Colors.grey),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 180,
          child: DecoratedBox(
            decoration: BoxDecoration(
              border: Border.all(color: colorScheme.outlineVariant),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Padding(
              padding: const EdgeInsets.all(8.0),
              child: CustomPaint(
                painter: _LineChartPainter(
                  x: x,
                  y: y,
                  lineColor: lineColor,
                  gridColor: colorScheme.outlineVariant.withAlpha(179),
                  textStyle: chartTextStyle,
                  yMinOverride: yMinOverride,
                  yMaxOverride: yMaxOverride,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _LineChartPainter extends CustomPainter {
  final List<double> x;
  final List<double> y;
  final Color lineColor;
  final Color gridColor;
  final TextStyle textStyle;
  final double? yMinOverride;
  final double? yMaxOverride;

  _LineChartPainter({
    required this.x,
    required this.y,
    required this.lineColor,
    required this.gridColor,
    required this.textStyle,
    this.yMinOverride,
    this.yMaxOverride,
  });

  @override
  void paint(Canvas canvas, Size size) {
    if (x.isEmpty || y.isEmpty || x.length != y.length) return;

    const leftPad = 48.0;
    const rightPad = 12.0;
    const topPad = 10.0;
    const bottomPad = 24.0;

    final plotRect = Rect.fromLTWH(
      leftPad,
      topPad,
      math.max(0, size.width - leftPad - rightPad),
      math.max(0, size.height - topPad - bottomPad),
    );
    if (plotRect.width <= 0 || plotRect.height <= 0) return;

    final xMinRaw = x.reduce(math.min);
    final xMaxRaw = x.reduce(math.max);

    final xMin = math.min(xMinRaw, 1.0);
    final xMax = math.max(xMaxRaw, xMin + 1.0);

    final yMinRaw = y.reduce(math.min);
    final yMaxRaw = y.reduce(math.max);

    double yMin = yMinOverride ?? yMinRaw;
    double yMax = yMaxOverride ?? yMaxRaw;

    if ((yMax - yMin).abs() < 1e-12) {
      yMin -= 1.0;
      yMax += 1.0;
    }

    final gridPaint = Paint()
      ..color = gridColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    final tickPaint = Paint()
      ..color = Colors.black
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    // Grid
    for (var i = 0; i <= 4; i++) {
      final t = i / 4.0;
      final yPos = plotRect.top + plotRect.height * t;
      canvas.drawLine(
          Offset(plotRect.left, yPos), Offset(plotRect.right, yPos), gridPaint);
    }

    canvas.drawRect(plotRect, gridPaint);

    double mapX(double xv) {
      if ((xMax - xMin).abs() < 1e-12) return plotRect.left;
      return plotRect.left + (xv - xMin) / (xMax - xMin) * plotRect.width;
    }

    double mapY(double yv) {
      return plotRect.bottom - (yv - yMin) / (yMax - yMin) * plotRect.height;
    }

    final path = Path();
    for (var i = 0; i < x.length; i++) {
      final p = Offset(mapX(x[i]), mapY(y[i]));
      if (i == 0) {
        path.moveTo(p.dx, p.dy);
      } else {
        path.lineTo(p.dx, p.dy);
      }
    }

    // 선 그리기
    canvas.drawPath(
        path,
        Paint()
          ..color = lineColor
          ..strokeWidth = 2
          ..style = PaintingStyle.stroke);

    // 🔥 추가된 부분: 데이터 포인트 원(Point) 그리기 (크기 3.0)
    final pointPaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.fill;

    for (var i = 0; i < x.length; i++) {
      final p = Offset(mapX(x[i]), mapY(y[i]));
      canvas.drawCircle(p, 3.0, pointPaint);
    }

    // 🔥 Y축: ymin / ymax만 표시
    _drawText(canvas, Offset(4, plotRect.top - 8), yMax.toStringAsFixed(3),
        textStyle);

    _drawText(canvas, Offset(4, plotRect.bottom - 12), yMin.toStringAsFixed(3),
        textStyle);

    // X ticks (1,5,10,...)
    const tickStep = 5.0;
    const eps = 1e-9;

    final ticks = <double>[];
    ticks.add(xMin);

    for (double t = tickStep; t <= xMax + eps; t += tickStep) {
      if ((t - xMin).abs() < eps) continue;
      if ((xMax - t).abs() < eps) continue;
      ticks.add(t);
    }

    if ((ticks.last - xMax).abs() > eps) {
      ticks.add(xMax);
    }

    for (final tick in ticks) {
      final tickX = mapX(tick);

      canvas.drawLine(
        Offset(tickX, plotRect.bottom),
        Offset(tickX, plotRect.bottom + 6),
        tickPaint,
      );

      final label = tick.toStringAsFixed(0);
      final tp = TextPainter(
        text: TextSpan(text: label, style: textStyle),
        textDirection: TextDirection.ltr,
      )..layout();

      double dx = tickX - tp.width / 2;
      if ((tick - xMin).abs() < eps) dx = plotRect.left;
      if ((tick - xMax).abs() < eps) dx = plotRect.right - tp.width;

      tp.paint(canvas, Offset(dx, plotRect.bottom + 6));
    }
  }

  void _drawText(Canvas canvas, Offset offset, String text, TextStyle style) {
    final tp = TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    )..layout();
    tp.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) {
    return true;
  }
}
