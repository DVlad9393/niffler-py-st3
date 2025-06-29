Собрать докер контейнеры:
cd niffler-py-st3
bash docker-compose-dev.sh

если необходимо настроить JAVA то выполнить команду:
export JAVA_HOME=$(/usr/libexec/java_home -v 21)
export PATH="$JAVA_HOME/bin:$PATH"
java -version
rm -rf ~/.gradle/caches
java -version
echo $JAVA_HOME
bash docker-compose-dev.sh

Запустить тесты с allure и удалением предыдущих результатов:
cd niffler_e_2_e_tests_python
rm -rf allure-results && python3 -m pytest niffler_e_2_e_tests_python  --alluredir=allure-results

Открыть отчёт:
allure serve
