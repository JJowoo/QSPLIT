import 'package:flutter/material.dart';

class HyperparameterConfig extends StatelessWidget {
  final TextEditingController nQubitsController;
  final TextEditingController batchSizeController;
  final TextEditingController deviceController;
  final TextEditingController epochsController;
  final TextEditingController optimizerController;
  final TextEditingController lrController;
  final int numberOfDummies;
  final Function(int) onNumberChanged;
  final VoidCallback onGeneratePressed;

  const HyperparameterConfig({
    super.key,
    required this.nQubitsController,
    required this.batchSizeController,
    required this.deviceController,
    required this.epochsController,
    required this.optimizerController,
    required this.lrController,
    required this.numberOfDummies,
    required this.onNumberChanged,
    required this.onGeneratePressed,
  });

  Widget _buildTextField(String label, TextEditingController controller) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: TextField(
        controller: controller,
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          isDense: true,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isNarrow = constraints.maxWidth < 650;

        return Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade600),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  const Text(
                    'Target Code Hyperparameter',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                  ),
                  ElevatedButton(
                    onPressed: onGeneratePressed,
                    child: const Text('Generate'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              isNarrow
                  ? Column(
                      children: [
                        _deviceSection(),
                        const SizedBox(height: 12),
                        _trainingSection(),
                      ],
                    )
                  : Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(child: _deviceSection()),
                        const SizedBox(width: 12),
                        Expanded(child: _trainingSection()),
                      ],
                    ),
              const SizedBox(height: 12),
              isNarrow
                  ? Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildDropdownContainer(
                          title: 'Dataset',
                          child: DropdownButton(
                            value: 'MedNIST',
                            items: ['MedNIST']
                                .map((e) =>
                                    DropdownMenuItem(value: e, child: Text(e)))
                                .toList(),
                            onChanged: (_) {},
                          ),
                        ),
                        const SizedBox(height: 12),
                        _buildDropdownContainer(
                          title: 'Number of Dummy Codes',
                          child: DropdownButton<int>(
                            value: numberOfDummies,
                            items: [1, 2, 3, 4, 5, 6]
                                .map((e) => DropdownMenuItem(
                                    value: e, child: Text('$e')))
                                .toList(),
                            onChanged: (val) => onNumberChanged(val!),
                          ),
                        ),
                      ],
                    )
                  : Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: _buildDropdownContainer(
                            title: 'Dataset',
                            child: DropdownButton(
                              value: 'MedNIST',
                              items: ['MedNIST']
                                  .map((e) => DropdownMenuItem(
                                      value: e, child: Text(e)))
                                  .toList(),
                              onChanged: (_) {},
                            ),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildDropdownContainer(
                            title: 'Number of Dummy Codes',
                            child: DropdownButton<int>(
                              value: numberOfDummies,
                              items: [1, 2, 3, 4, 5, 6]
                                  .map((e) => DropdownMenuItem(
                                      value: e, child: Text('$e')))
                                  .toList(),
                              onChanged: (val) => onNumberChanged(val!),
                            ),
                          ),
                        ),
                      ],
                    ),
            ],
          ),
        );
      },
    );
  }

  Widget _deviceSection() {
    return _buildSection(
      title: 'Quantum Device',
      children: [
        _buildTextField('n_qubits', nQubitsController),
        _buildTextField('batch_size', batchSizeController),
        _buildTextField('to_device', deviceController),
      ],
    );
  }

  Widget _trainingSection() {
    return _buildSection(
      title: 'Training',
      children: [
        _buildTextField('epochs', epochsController),
        _buildTextField('optimizer', optimizerController),
        _buildTextField('learning rate', lrController),
      ],
    );
  }

  Widget _buildSection(
      {required String title, required List<Widget> children}) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.blueGrey.shade800.withOpacity(0.4),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...children,
        ],
      ),
    );
  }

  Widget _buildDropdownContainer(
      {required String title, required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: Colors.blueGrey.shade800.withOpacity(0.4),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Text('$title: '),
          const SizedBox(width: 10),
          child,
        ],
      ),
    );
  }
}
