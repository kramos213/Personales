#include <iostream>
using namespace std;

int main() {
    const int DIAS = 28;
    double ventas[DIAS];
    bool registrado = false;
    int opcion;

    do {
        cout << "\n===== MENU =====\n";
        cout << "1. Ingresar ventas\n";
        cout << "2. Mostrar reporte\n";
        cout << "3. Reiniciar datos\n";
        cout << "4. Salir\n";
        cout << "Seleccione una opcion: ";
        cin >> opcion;

        if (opcion == 1) {
            // Ingresar ventas
            for (int i = 0; i < DIAS; i++) {
                cout << "Venta del dia " << (i + 1) << ": ";
                cin >> ventas[i];
            }
            registrado = true;
        }

        else if (opcion == 2) {
            if (!registrado) {
                cout << "Debe ingresar las ventas primero.\n";
            } else {
                double total = 0;
                double mayor = ventas[0];
                double menor = ventas[0];
                
                int diaMayor = 1, diaMenor = 1;

                for (int i = 0; i < DIAS; i++) {
                    total += ventas[i];

                    if (ventas[i] > mayor) {
                        mayor = ventas[i];
                        diaMayor = i + 1;
                    }
                    if (ventas[i] < menor) {
                        menor = ventas[i];
                        diaMenor = i + 1;
                    }
                }

                double promedioDiario = total / 28;
                double promedioSemanal = total / 4;
                double comision;

                if (total > 80000)
                    comision = total * 0.10;
                else
                    comision = total * 0.05;

                cout << "\n===== REPORTE =====\n";
                cout << "Total mensual: " << total << endl;
                cout << "Promedio diario: " << promedioDiario << endl;
                cout << "Dia con mayor venta: " << diaMayor << " (" << mayor << ")\n";
                cout << "Dia con menor venta: " << diaMenor << " (" << menor << ")\n";
                cout << "Promedio semanal: " << promedioSemanal << endl;
                cout << "Comision: " << comision << endl;
            }
        }

        else if (opcion == 3) {
            registrado = false;
            cout << "Datos reiniciados.\n";
        }

        else if (opcion == 4) {
            cout << "Saliendo...\n";
        }

        else {
            cout << "Opcion invalida.\n";
        }

    } while (opcion != 4);

    return 0;
}
