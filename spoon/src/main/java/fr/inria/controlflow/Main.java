package fr.inria.controlflow;

import java.io.IOException;
import java.nio.charset.Charset;
import java.util.*;

import java.util.regex.Matcher;
import java.util.regex.Pattern;


import com.csvreader.CsvReader;
import com.csvreader.CsvWriter;

import spoon.reflect.cu.SourcePosition;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtElement;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtType;
import spoon.reflect.factory.Factory;
import spoon.reflect.visitor.CtIterator;
import spoon.support.compiler.VirtualFile;
import spoon.Launcher;
class CFG{
	ControlFlowGraph cfg;
	int target;
	CFG(ControlFlowGraph cfg, int target){
		this.cfg = cfg;
		this.target = target;
	}
}
public class Main {

	public static fr.inria.controlflow.CFG getCFG(String code, int start, int end){

		code = "class A {\n "+code+"}";
		start += 11;
		end += 11;
		code = code.replaceAll("(_)(\\()", " $2");
//		code = code.replaceAll("(\\(\\s+;)(\\s+)(;\\s+\\))", "$1T$3");
		code = code.replaceAll("\\$", "R");


		Launcher launcher = new Launcher();
		launcher.addInputResource(new VirtualFile(code));
		launcher.getEnvironment().setNoClasspath(true);
		launcher.getEnvironment().setAutoImports(true);
		try{
			launcher.buildModel();
		}catch (Exception e) {
			System.out.println(code);
		}

		final Factory factory = launcher.getFactory();


		for (CtType<?> type : factory.Class().getAll()) {
			if (type.isInterface() || type.isAnnotationType())
				continue;
			CtClass clazz = (CtClass) type;
			Set<CtMethod> methodSet = clazz.getAllMethods();
			for (CtMethod method : methodSet) {
				//cfgConstruct(method);
				if(method.isShadow())
					continue;
				if (method == null || method.getBody() == null) {
					continue;
				}

				ControlFlowBuilder builder = new ControlFlowBuilder();

				EnumSet<NaiveExceptionControlFlowStrategy.Options> options;
				options = EnumSet.of(NaiveExceptionControlFlowStrategy.Options.ReturnWithoutFinalizers);

				builder.setExceptionControlFlowStrategy(new NaiveExceptionControlFlowStrategy(options));

				ControlFlowGraph graph = builder.build(method);
				graph.simplify();
				int id = 0;
//	            System.out.println(method.getSimpleName()+"\n");
//	            System.out.println(graph.toGraphVisText());
				for (ControlFlowNode n : graph.vertexSet()) {
					id++;
					if(n.getStatement() != null){
//						System.out.println(n.getStatement().toString());
						SourcePosition position = n.getStatement().getPosition();
						try {
							if (Math.max(position.getSourceStart(), start) < Math.min(position.getSourceEnd() + 1, end)) {
								return new CFG(graph, id);
							}
						}catch (UnsupportedOperationException uoe){
							System.out.println(uoe.toString());
						}
					}
				}

			}
		}
		return null;
	}
	public static int findNode(ControlFlowGraph graph, int start, int end){
		start += 11;
		end += 11;
		int id = 0;
//	            System.out.println(method.getSimpleName()+"\n");
//	            System.out.println(graph.toGraphVisText());
		for (ControlFlowNode n : graph.vertexSet()) {
			id++;
			if(n.getStatement() != null){
//						System.out.println(n.getStatement().toString());
				SourcePosition position = n.getStatement().getPosition();
				try {
					if (Math.max(position.getSourceStart(), start) < Math.min(position.getSourceEnd() + 1, end)) {
						return id;
					}
				}catch (UnsupportedOperationException uoe){
					System.out.println(uoe.toString());
				}
			}
		}
		return -1;
	}
	public static void main(String[] args) throws IOException {
		CsvReader csvReader = new CsvReader(args[0], ',', Charset.forName("UTF-8"));
		CsvWriter csvWriter = new CsvWriter(args[1], ',', Charset.forName("UTF-8"));
		csvReader.readHeaders();
		String[]  headers = {"id", "method", "cfg", "target", "node", "label"};
		csvWriter.writeRecord(headers);
		String lastCodeId = "";
		ControlFlowGraph graph = null;
		Pattern pattern = Pattern.compile("\\d+");
		csvReader.setSafetySwitch(false);
		while (csvReader.readRecord()) {
			String codeId = csvReader.get("id");
			System.out.println(codeId);
			String code = csvReader.get("method");
			String target = csvReader.get("target");

			Matcher matcher = pattern.matcher(target);
			List<String> positions = new ArrayList<>();
			while (matcher.find()) {
				positions.add(matcher.group());
			}
			int start = Integer.parseInt(positions.get(0));
			int end = Integer.parseInt(positions.get(1))+1;
			int nodeId;
			try {
				if(codeId.equals(lastCodeId)){
					if(graph == null)
						continue;
					nodeId = findNode(graph, start, end);
				}else {
					CFG result = getCFG(code, start, end);

					if (result == null) {
						graph = null;
//							System.out.println(code);
//							System.out.println(target);
//							System.out.println(code.substring(start, end));
//							continue;
						nodeId = -1;
					} else {
						nodeId = result.target;
						graph = result.cfg;
					}
					lastCodeId = codeId;
				}
				if(graph != null && nodeId != -1) {
					String[] content = {codeId, '"' + code + '"', '"' + graph.toGraphVisText() + '"', target, nodeId + "", csvReader.get("label")};
					csvWriter.writeRecord(content);
				}
			}catch (Exception e){
				System.out.println(code);
			}

		}
		csvWriter.close();

	}

}
