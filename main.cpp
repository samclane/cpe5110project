#include <stdlib.h>
#include <iostream>
#include <stdio.h> 
#include <string>
#include <cstring>
#include <fstream>
#include <vector>
using namespace std;


int main (int argc, char** argv)
{
	string inputBuffer[10000];
	string temp;
	int instrCount, memoryCount;
	int index;
	ifstream in_stream;
	try 
	{
		in_stream.open(argv[1]);
	}
	catch (ifstream::failure e) 
	{
		cerr << "Exception reading/opening file\n";
	}
	while(!in_stream.eof())
	{
		getline(in_stream,temp);
		if (48 <= ((temp[0]-'0') + 48) && ((temp[0]-'0') + 48) <= 57)
		{
			//first value is a number
			int index2 = 0;
			string tempNum = "";
			while(temp[index2] != ' ')
			{
				strcat(tempNum, temp[index2]);
			}
			instrCount = tempNum;
			cout << "myval " << ((temp[0]-'0') + 48) << endl;
		} 
		index++;
	}
	in_stream.close();



	for (int i = 0; i < 0; i++)
	{
		cout << inputBuffer[i] << endl;
	}
}


