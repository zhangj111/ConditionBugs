package fr.inria.controlflow;

import java.io.IOException;
import java.nio.charset.Charset;
import java.util.EnumSet;
import java.util.Set;

import com.csvreader.CsvReader;
import fr.inria.controlflow.ControlFlowBuilder;
import fr.inria.controlflow.ControlFlowGraph;
import fr.inria.controlflow.ControlFlowNode;
import fr.inria.controlflow.NaiveExceptionControlFlowStrategy;
import spoon.Launcher;
import spoon.reflect.code.CtTryWithResource;
import spoon.reflect.cu.SourcePosition;
import spoon.reflect.declaration.CtClass;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.declaration.CtType;
import spoon.reflect.factory.Factory;
import spoon.support.compiler.VirtualFile;


public class Parser {
	public static void count() throws IOException {
		CsvReader csvReader = new CsvReader("E:\\java\\spoon\\cfgs.csv", ',', Charset.forName("UTF-8"));
		csvReader.readHeaders();
		csvReader.setSafetySwitch(false);
		int size=0;
		while (csvReader.readRecord()) {
			size += 1;
		}
		System.out.println(size);
	}
	public static void main(String[] args) throws IOException{
		count();
		System.exit(-1);
		// TODO Auto-generated method stub
		String code = "class A {\n "+
			    " boolean isWildcardRef(Expression expr) {\n" +
				"    VariableExpression varExpr = AstUtil.asInstance(expr, VariableExpression.class);\n" +
				"    if (varExpr == null || !varExpr.getName().equals(Specification._.toString())) return false;\n" +
				"\n" +
				"    Variable accessedVar = varExpr.getAccessedVariable();\n" +
				"    if (accessedVar instanceof FieldNode) \n" +
				"      return ((FieldNode) accessedVar).getOwner().getName().equals(Specification.class.getName());\n" +
				"\n" +
				"    if (accessedVar instanceof DynamicVariable) \n" +
				"      \n" +
				"      return true;\n" +
				"\n" +
				"    return false;\n" +
				"  }" +
	         "}";
		code = code.replaceAll("(_)(\\()", " $2");
		code = code.replaceAll("(\\(\\s+;)(\\s+)(;\\s+\\))", "$1T$3");
		code = code.replaceAll("\\$", "R");
		System.out.println(code);
		Launcher launcher = new Launcher();
		launcher.addInputResource(new VirtualFile(code));
		launcher.getEnvironment().setNoClasspath(true);
		launcher.getEnvironment().setAutoImports(true);
		launcher.buildModel();
		
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
		        System.out.println(method.getSimpleName()+"\n");
	            System.out.println(graph.toGraphVisText());

				
			}
		}
	}

}
