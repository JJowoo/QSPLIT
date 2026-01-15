// results_panel.dart
import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'training_history_chart.dart';

class ResultsPanel extends StatelessWidget {
  final List<Map<String, dynamic>> dummyData;
  final VoidCallback? onExport;

  const ResultsPanel({
    super.key,
    required this.dummyData,
    this.onExport,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Results', style: textTheme.titleLarge),
            const SizedBox(height: 8),
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  // DataTable은 좁은 폭에서 쉽게 overflow가 나므로
                  // (1) 세로 스크롤, (2) 가로 스크롤을 모두 허용한다.
                  return SingleChildScrollView(
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: ConstrainedBox(
                        constraints: BoxConstraints(
                            minWidth: math.max(constraints.maxWidth, 720)),
                        child: DataTable(
                          headingRowColor: WidgetStateProperty.all(
                            Theme.of(context).colorScheme.primary.withAlpha(26),
                          ),
                          columnSpacing: 24,
                          columns: const [
                            DataColumn(
                              label: Tooltip(
                                message: 'Dummy Code',
                                child: Text('Dummy Code',
                                    overflow: TextOverflow.ellipsis),
                              ),
                            ),
                            DataColumn(
                              label: Tooltip(
                                message: 'Accuracy',
                                child: Text('Accuracy',
                                    overflow: TextOverflow.ellipsis),
                              ),
                            ),
                            DataColumn(
                              label: Tooltip(
                                message: 'Train Time',
                                child: Text('Train Time',
                                    overflow: TextOverflow.ellipsis),
                              ),
                            ),
                            DataColumn(
                              label: Tooltip(
                                message: 'History',
                                child: Text('History',
                                    overflow: TextOverflow.ellipsis),
                              ),
                            ),
                          ],
                          rows: dummyData.asMap().entries.map((entry) {
                            final idx = entry.key;
                            final dummy = entry.value;
                            final accuracy =
                                dummy['accuracy'] as double? ?? 0.0;
                            final trainSeconds =
                                dummy['train_seconds'] as double? ?? 0.0;
                            final history = (dummy['history'] as List<dynamic>?)
                                    ?.cast<Map<String, dynamic>>() ??
                                const <Map<String, dynamic>>[];
                            return DataRow(
                              cells: [
                                DataCell(Text('Dummy#${idx + 1}',
                                    overflow: TextOverflow.ellipsis)),
                                DataCell(Text(accuracy.toStringAsFixed(3))),
                                DataCell(Text(
                                    '${trainSeconds.toStringAsFixed(2)}s')),
                                DataCell(
                                  history.isEmpty
                                      ? const Text('-')
                                      : IconButton(
                                          tooltip: 'View history chart',
                                          onPressed: () {
                                            showDialog<void>(
                                              context: context,
                                              builder: (ctx) => AlertDialog(
                                                title: Text('Dummy#${idx + 1}'),
                                                content: SizedBox(
                                                  width: (() {
                                                    final w = MediaQuery.of(ctx)
                                                        .size
                                                        .width;
                                                    final target = w * 0.9;
                                                    final v = target < 640
                                                        ? target
                                                        : 640;
                                                    return v.toDouble();
                                                  })(),
                                                  child: TrainingHistoryChart(
                                                      history: history),
                                                ),
                                                actions: [
                                                  TextButton(
                                                    onPressed: () =>
                                                        Navigator.of(ctx).pop(),
                                                    child: const Text('Close'),
                                                  ),
                                                ],
                                              ),
                                            );
                                          },
                                          icon: const Icon(Icons.show_chart),
                                        ),
                                ),
                              ],
                            );
                          }).toList(),
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                ElevatedButton.icon(
                  onPressed: onExport ??
                      () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                              content: Text('Export in progress...')),
                        );
                      },
                  icon: const Icon(Icons.save_alt),
                  label: const Text('Export'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
