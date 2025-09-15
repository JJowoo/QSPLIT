// results_panel.dart
import 'package:flutter/material.dart';

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
              child: SingleChildScrollView(
                child: DataTable(
                  headingRowColor: WidgetStateProperty.all(
                    Theme.of(context).colorScheme.primary.withOpacity(0.1),
                  ),
                  columns: const [
                    DataColumn(label: Text('Dummy Code')),
                    DataColumn(label: Text('Accuracy')),
                  ],
                  rows: dummyData.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final dummy = entry.value;
                    final dummyId = dummy['dummy_id'] as String;
                    final accuracy = dummy['accuracy'] as double? ?? 0.0;
                    return DataRow(
                      cells: [
                        DataCell(Text('Dummy#${idx + 1}')),
                        DataCell(Text(accuracy.toStringAsFixed(3))),
                      ],
                    );
                  }).toList(),
                ),
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
