import net.sf.jasperreports.engine.JasperCompileManager;
import net.sf.jasperreports.engine.JasperFillManager;
import net.sf.jasperreports.engine.JasperExportManager;
import net.sf.jasperreports.engine.JasperReport;
import net.sf.jasperreports.engine.JasperPrint;
import net.sf.jasperreports.engine.util.JRLoader;
import net.sf.jasperreports.engine.data.JRXmlDataSource;
import net.sf.jasperreports.engine.util.JRXmlUtils;
import net.sf.jasperreports.engine.query.JRXPathQueryExecuterFactory;
import net.sf.jasperreports.engine.JRQuery;
import net.sf.jasperreports.view.JasperViewer;
import org.w3c.dom.Document;
import java.sql.*;
import java.util.*;
import java.io.FileInputStream;

public class ReportCreator {

  public static void createReport( String reportFile, String xmlFile, String reportOutput, Connection con , HashMap params )
	{
		try {
			System.out.println( "Src: '" + reportFile + "'");
			System.out.println( "Xml: '" + xmlFile + "'");
			System.out.println( "Dst: '" + reportOutput + "'");
			System.out.println( "params: '" + params + "'");

			JasperReport report;
			JRQuery query;
			JasperPrint jasperPrint=null;
			
			report = (JasperReport) JRLoader.loadObject( reportFile );
			query = report.getQuery();
			
			Map parameters = params;
			//parameters.put(JRXPathQueryExecuterFactory.PARAMETER_XML_DATA_DOCUMENT, document);
			//parameters.put(JRXPathQueryExecuterFactory.XML_DATE_PATTERN, "yyyy-MM-dd");
			//parameters.put(JRXPathQueryExecuterFactory.XML_NUMBER_PATTERN, "#,##0.##");
			//parameters.put(JRXPathQueryExecuterFactory.XML_LOCALE, Locale.ENGLISH);


			System.out.println("LANGUAGE:" + query.getLanguage());
			if( query.getLanguage().equalsIgnoreCase(  "XPATH")  ){
				System.out.println("XPATH");
				JRXmlDataSource dataSource = new JRXmlDataSource( xmlFile, "/data/record" );
				jasperPrint = JasperFillManager.fillReport( report, parameters, dataSource );
			} else if(  query.getLanguage().equalsIgnoreCase( "SQL")  ) {
				System.out.println("2-SQL");
				System.out.println("Parameters:" + parameters.toString() );
				jasperPrint = JasperFillManager.fillReport( report, parameters, con );
			}
		    
			JasperExportManager.exportReportToPdfFile( jasperPrint, reportOutput );
		} catch (Exception e){
		  e.printStackTrace();
		  System.out.println( e.getMessage() );
		}
	}

	public static Connection getConnection(String dsn, String user, String password) throws java.lang.ClassNotFoundException, java.sql.SQLException
	{
		Connection connection;
		Class.forName("org.postgresql.Driver");

		System.out.println("DSN: " + dsn);
		connection = DriverManager.getConnection( dsn, user, password );
		connection.setAutoCommit(false);
		System.out.println( "colsed:" + connection.isClosed() );
		return connection;
	}

	public static HashMap parseParams( String params ){
		HashMap parameters= new HashMap();
		System.out.println( "Params:" + params );
		String[] p = params.split(";");
		for( int j=0; j < p.length ; j++ ){
			System.out.println( p[j] );
			String[] map = p[j].split(":");
			parameters.put( map[0] , map[1] );
		}
		System.out.println( parameters );
		return parameters;
	}

	public static void main( String[] args ) 
	{
		for( int i=0;i< args.length; i++ )
			System.out.println( "arguments:" + args[i]);

		Connection con=null;
		HashMap parameters;

		if ( args.length >= 3 ) {  
			String dsn = args[3];
			String user=args[4];
			String password=args[5];
			String params = args[6];
			try {
				con = getConnection( dsn,user,password );
			} catch( Exception e ){
				e.printStackTrace();
			}
			parameters = parseParams( params );
			createReport( args[0], args[1], args[2] , con, parameters );
		} else
			System.out.println( "Three arguments needed." );
	}
}

