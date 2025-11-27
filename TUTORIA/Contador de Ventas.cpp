#include <iostream>
using namespace std;

int main() {
    const int DIAS = 28;

    double total = 0;
    double mayor = 0;
    double menor = 0;
    int diaMayor = 0;
    int diaMenor = 0;

    int datosIngresados = 0;
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
            // Reiniciar acumuladores para nueva entrada
            total = 0;
            mayor = 0;
            menor = 0;
            diaMayor = 0;
            diaMenor = 0;

            double venta;

            for (int i = 1; i <= DIAS; i++) {
                cout << "Venta del dia " << i << ": ";
                cin >> venta;

                total += venta;

                if (i == 1) { 
                    mayor = venta;
                    menor = venta;
                    diaMayor = 1;
                    diaMenor = 1;
                }

                if (venta > mayor) {
                    mayor = venta;
                    diaMayor = i;
                }

                if (venta < menor) {
                    menor = venta;
                    diaMenor = i;
                }
            }

            datosIngresados = 1;
        }

        else if (opcion == 2) {
            if (datosIngresados == 0) {
                cout << "Debe ingresar las ventas primero.\n";
            } else {
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
            datosIngresados = 0;
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
