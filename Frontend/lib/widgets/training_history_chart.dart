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
      return const Text('No training history is available.');
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

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(title, style: textTheme.titleMedium),
        const SizedBox(height: 4),
        Text(subtitle,
            style: textTheme.bodySmall?.copyWith(color: Colors.grey)),
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
                  textStyle: textTheme.labelSmall ??
                      const TextStyle(fontSize: 10, color: Colors.grey),
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

    const leftPad = 34.0;
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

    // Ensure X-axis starts at 1.0 (or 0.0 if data contains it)
    final xMin = math.min(xMinRaw, 1.0);
    // Ensure at least 1 epoch range for better visualization
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

    // Horizontal grid (4 lines)
    for (var i = 0; i <= 4; i++) {
      final t = i / 4.0;
      final yPos = plotRect.top + plotRect.height * t;
      canvas.drawLine(
          Offset(plotRect.left, yPos), Offset(plotRect.right, yPos), gridPaint);
    }

    // Border
    canvas.drawRect(plotRect, gridPaint);

    double mapX(double xv) {
      if ((xMax - xMin).abs() < 1e-12) return plotRect.left;
      return plotRect.left + (xv - xMin) / (xMax - xMin) * plotRect.width;
    }

    double mapY(double yv) {
      return plotRect.bottom - (yv - yMin) / (yMax - yMin) * plotRect.height;
    }

    final linePaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.0;

    final pointPaint = Paint()
      ..color = lineColor
      ..style = PaintingStyle.fill;

    final path = Path();
    for (var i = 0; i < x.length; i++) {
      final p = Offset(mapX(x[i]), mapY(y[i]));
      if (i == 0) {
        path.moveTo(p.dx, p.dy);
      } else {
        path.lineTo(p.dx, p.dy);
      }
    }
    canvas.drawPath(path, linePaint);

    // Points
    for (var i = 0; i < x.length; i++) {
      final p = Offset(mapX(x[i]), mapY(y[i]));
      canvas.drawCircle(p, 3.0, pointPaint);
    }

    // Labels (min/max + first/last epoch)
    _drawText(
      canvas,
      Offset(0, plotRect.top - 2),
      _formatNumber(yMax, 3),
      textStyle,
    );
    _drawText(
      canvas,
      Offset(0, plotRect.bottom - 10),
      _formatNumber(yMin, 3),
      textStyle,
    );

    _drawText(
      canvas,
      Offset(plotRect.left, plotRect.bottom + 6),
      _formatNumber(xMin, 0),
      textStyle,
    );
    final lastLabel = _formatNumber(xMax, 0);
    final lastTp = _textPainter(lastLabel, textStyle)..layout();
    _drawText(
      canvas,
      Offset(plotRect.right - lastTp.width, plotRect.bottom + 6),
      lastLabel,
      textStyle,
    );
  }

  String _formatNumber(double v, int fractionDigits) {
    return v.toStringAsFixed(fractionDigits);
  }

  TextPainter _textPainter(String text, TextStyle style) {
    return TextPainter(
      text: TextSpan(text: text, style: style),
      textDirection: TextDirection.ltr,
    );
  }

  void _drawText(Canvas canvas, Offset offset, String text, TextStyle style) {
    final tp = _textPainter(text, style)..layout();
    tp.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant _LineChartPainter oldDelegate) {
    return oldDelegate.x != x ||
        oldDelegate.y != y ||
        oldDelegate.lineColor != lineColor ||
        oldDelegate.gridColor != gridColor ||
        oldDelegate.textStyle != textStyle ||
        oldDelegate.yMinOverride != yMinOverride ||
        oldDelegate.yMaxOverride != yMaxOverride;
  }
}
