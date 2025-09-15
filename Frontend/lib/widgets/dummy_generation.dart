import 'package:flutter/material.dart';

class DummyGeneration extends StatelessWidget {
  final List<String> dummyList;
  final List<Map<String, dynamic>> dummyData;
  final String selectedDummyCode;
  final Set<String> selectedDummyCodes; // 추가: PartSelection에서 선택된 Dummy Code들
  final VoidCallback onRunPressed;
  final Function(String) onDummyCodeChanged;

  const DummyGeneration({
    super.key,
    required this.dummyList,
    required this.dummyData,
    required this.selectedDummyCode,
    required this.selectedDummyCodes,
    required this.onRunPressed,
    required this.onDummyCodeChanged,
  });

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final colorScheme = Theme.of(context).colorScheme;
    // 선택된 더미의 info에서 존재하는 파트만 추출
    final selectedDummy = dummyData.firstWhere(
        (e) => e['dummy_id'] == selectedDummyCode,
        orElse: () => <String, dynamic>{'info': <String, dynamic>{}});
    final info = selectedDummy['info'] as Map<String, dynamic>? ?? {};
    final infoKeys = info.keys.map((k) => k.toString().toUpperCase()).toSet();
    final orderedCodes =
        ['SE', 'PQC', 'MEA'].where((code) => infoKeys.contains(code)).toList();

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Dummy Code Generation', style: textTheme.titleLarge),
                ElevatedButton(
                    onPressed: onRunPressed, child: const Text('Run')),
              ],
            ),
            const SizedBox(height: 20),
            Expanded(
              child: Center(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Dummy List
                    Container(
                      width: 150,
                      height: 250,
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: colorScheme.surfaceContainerHighest
                            .withOpacity(0.3),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding:
                                const EdgeInsets.only(left: 8.0, bottom: 4.0),
                            child:
                                Text("Dummy List", style: textTheme.titleSmall),
                          ),
                          Expanded(
                            child: ListView.builder(
                              itemCount: dummyList.length,
                              itemBuilder: (context, idx) {
                                final dummy = dummyList[idx];
                                return Row(
                                  children: [
                                    Radio<String>(
                                      value: dummy,
                                      groupValue: selectedDummyCode,
                                      onChanged: (val) {
                                        if (val != null) {
                                          onDummyCodeChanged(val);
                                        }
                                      },
                                    ),
                                    Expanded(child: Text('Dummy#${idx + 1}')),
                                  ],
                                );
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Visualization + Details
                    Expanded(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: orderedCodes
                            .asMap()
                            .entries
                            .map((entry) {
                              final index = entry.key;
                              final code = entry.value;
                              final isGood = code == 'PQC' || code == 'SE';
                              return [
                                if (index > 0)
                                  const SizedBox(width: 20), // 파트 간 간격
                                Expanded(
                                  child: Row(
                                    children: [
                                      // 좌측 이미지
                                      Container(
                                        height: 250,
                                        width: 120,
                                        margin:
                                            const EdgeInsets.only(right: 12),
                                        child: Image.asset(
                                          _getImagePath(code),
                                          fit: BoxFit.contain,
                                        ),
                                      ),
                                      // 정보 박스
                                      Expanded(
                                        child: Container(
                                          height: 250,
                                          padding: const EdgeInsets.all(12),
                                          decoration: BoxDecoration(
                                            borderRadius:
                                                BorderRadius.circular(10),
                                            border: Border.all(
                                              color: isGood
                                                  ? Colors.green.shade200
                                                  : Colors.grey.shade400,
                                            ),
                                            color: isGood
                                                ? Colors.green.shade50
                                                    .withOpacity(0.5)
                                                : Colors.grey.shade200
                                                    .withOpacity(0.5),
                                          ),
                                          child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(
                                                code,
                                                style: textTheme.titleMedium
                                                    ?.copyWith(
                                                  color: isGood
                                                      ? Colors.green.shade900
                                                      : Colors.grey.shade800,
                                                ),
                                              ),
                                              const Divider(),
                                              ..._buildCodeDetails(
                                                  context, code),
                                            ],
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ];
                            })
                            .expand((widgets) => widgets)
                            .toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _getImagePath(String code) {
    switch (code) {
      case 'SE':
        return 'resources/image/Encoder.png';
      case 'PQC':
        return 'resources/image/PQC.png';
      case 'MEA':
        return 'resources/image/MEA.png';
      default:
        return 'resources/image/Encoder.png'; // 기본값
    }
  }

  List<Widget> _buildCodeDetails(BuildContext context, String code) {
    final textStyle = Theme.of(context).textTheme.bodySmall;
    final selectedDummy = dummyData.firstWhere(
        (e) => e['dummy_id'] == selectedDummyCode,
        orElse: () => <String, dynamic>{'info': <String, dynamic>{}});
    final info = selectedDummy['info'] as Map<String, dynamic>? ?? {};
    final partInfo = info[code.toLowerCase()];
    if (partInfo is Map<String, dynamic>) {
      return partInfo.entries.map<Widget>((entry) {
        return Text('• ${entry.key} : ${entry.value}', style: textStyle);
      }).toList();
    }
    return [];
  }
}
